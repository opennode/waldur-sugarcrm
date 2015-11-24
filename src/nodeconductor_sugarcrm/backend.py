import logging
import md5
import urlparse

import requests
from rest_framework.reverse import reverse
import sugarcrm

from nodeconductor.core.tasks import send_task
from nodeconductor.core.utils import pwgen
from nodeconductor.structure import ServiceBackend, ServiceBackendError


logger = logging.getLogger(__name__)


class SugarCRMBackendError(ServiceBackendError):
    pass


class SugarCRMBackend(object):

    def __init__(self, settings, *args, **kwargs):
        backend_class = SugarCRMDummyBackend if settings.dummy else SugarCRMRealBackend
        self.backend = backend_class(settings, *args, **kwargs)

    def __getattr__(self, name):
        return getattr(self.backend, name)


class SugarCRMBaseBackend(ServiceBackend):

    def provision(self, crm):
        send_task('sugarcrm', 'provision_crm')(
            crm.uuid.hex,
        )

    def destroy(self, crm):
        # CRM cannot be stopped by user - so we need to stop it before deletion on destroy
        crm.schedule_stopping()
        crm.save()
        send_task('sugarcrm', 'stop_and_destroy_crm')(
            crm.uuid.hex,
        )


class SugarCRMRealBackend(SugarCRMBaseBackend):
    """ Sugar CRM backend methods

    Backend uses two clients for operations:
    1. NodeCondcutor OpenStack client uses to NC OpenStack application endpoints for operations with SugarCRM VM.
    2. SugarCRM client interacts with SugarCRM API.
    """

    DEFAULT_USER_DATA = ("#cloud-config:\n"
                         "runcmd:\n"
                         "  - [ bootstrap, -p, {adminpass}]")
    DEFAULT_PROTOCOL = 'http'
    CRM_ADMIN_NAME = 'admin'

    class NodeConductorOpenStackClient(object):

        def __init__(self, template_url, username, password):
            self.credentials = {
                'username': username,
                'password': password,
            }
            parsed = urlparse.urlparse(template_url)
            self.scheme = parsed.scheme
            self.netloc = parsed.netloc

        def authenticate(self):
            url = self._prepare_url(reverse('auth-password'))
            response = requests.post(url, data=self.credentials, verify=False)
            if response.ok:
                self.token = response.json()['token']
            else:
                raise SugarCRMBackendError('Cannot authenticate as %s' % self.credentials['username'])

        def _prepare_url(self, url):
            """ Add scheme, host and port to url """
            if not url.startswith('http'):
                return urlparse.urlunsplit([self.scheme, self.netloc, url, '', ''])
            return url

        def _make_request(self, method, url, retry_if_authentication_fails=True, **kwargs):
            if not hasattr(self, 'token'):
                self.authenticate()
            headers = kwargs.get('headers', {})
            headers['Authorization'] = 'Token %s' % self.token
            kwargs['headers'] = headers
            kwargs['verify'] = kwargs.get('verify', False)

            url = self._prepare_url(url)
            response = getattr(requests, method)(url, **kwargs)
            if response.status_code == requests.status_codes.codes.unauthorized and retry_if_authentication_fails:
                return self._make_request(method, url, retry_if_authentication_fails=False, **kwargs)
            else:
                return response

        def get(self, url, **kwargs):
            return self._make_request('get', url, **kwargs)

        def post(self, url, **kwargs):
            return self._make_request('post', url, **kwargs)

        def delete(self, url, **kwargs):
            return self._make_request('delete', url, **kwargs)

    class SugarCRMClient(object):

        def __init__(self, url, username, password):
            self.url = url + '/service/v4/rest.php'
            self.session = sugarcrm.Session(self.url, username, password)

        def create_user(self, **kwargs):
            user = sugarcrm.User()
            for key, value in kwargs.items():
                setattr(user, key, value)
            return self.session.set_entry(user)

        def get_user(self, user_id):
            return self.session.get_entry('Users', user_id)

        def list_users(self):
            user_query = sugarcrm.User()
            return self.session.get_entry_list(user_query)

        def delete_user(self, user):
            user.deleted = 1
            self.session.set_entry(user)

    def __init__(self, settings, crm=None):
        self.template_url = settings.backend_url
        self.options = settings.options or {}
        self.nc_client = self.NodeConductorOpenStackClient(self.template_url, settings.username, settings.password)
        self.crm = crm

    @property
    def sugar_client(self):
        if hasattr(self, '_sugar_client'):
            return self._sugar_client
        if self.crm is None:
            raise SugarCRMBackendError('It is impossible to use sugar client if CRM is not specified for backend.')
        self._sugar_client = self.SugarCRMClient(self.crm.api_url, self.crm.admin_username, self.crm.admin_password)
        return self._sugar_client

    def schedule_crm_instance_provision(self, crm):
        # prepare data for template group provisioning
        user_data = self.options.get('user_data', self.DEFAULT_USER_DATA)
        admin_username = self.CRM_ADMIN_NAME
        admin_password = pwgen()
        user_data = user_data.format(password=admin_password)

        template_data = [{
            'name': crm.name,
            'user_data': user_data,
        }]
        # schedule template provisioning
        response = self.nc_client.post(self.template_url + 'provision/', json=template_data)
        if not response.ok:
            raise SugarCRMBackendError(
                'Cannot provision OpenStack instance for CRM "%s": response code - %s, response content: %s.'
                'Request URL: %s, request body: %s' %
                (crm.name, response.status_code, response.content, response.request.url, response.request.body))
        # store template group result as backend_id
        crm.admin_password = admin_password
        crm.admin_username = admin_username
        crm.backend_id = response.json()['result_url']
        crm.save()

        logger.info('Successfully scheduled instance provision for CRM "%s"', crm.name)

    def schedule_crm_instance_stopping(self, crm):
        instance_url = self.get_crm_instance_url(crm)
        response = self.nc_client.post(instance_url + 'stop/')
        if not response.ok:
            raise SugarCRMBackendError(
                'Cannot stop OpenStack instance for CRM "%s": response code - %s, response content: %s.'
                'Request URL: %s, request body: %s' %
                (crm.name, response.status_code, response.content, response.request.url, response.request.body))

        logger.info('Successfully scheduled instance stopping for CRM "%s"', crm.name)

    def schedule_crm_instance_deletion(self, crm):
        instance_url = self.get_crm_instance_url(crm)
        response = self.nc_client.delete(instance_url)
        if not response.ok:
            raise SugarCRMBackendError(
                'Cannot delete OpenStack instance for CRM "%s": response code - %s, response content: %s.'
                'Request URL: %s, request body: %s' %
                (crm.name, response.status_code, response.content, response.request.url, response.request.body))

        logger.info('Successfully scheduled instance deletion for CRM "%s"', crm.name)

    def get_crm_instance_details(self, crm):
        """ Get details of instance that corresponds given CRM """
        instance_url = self.get_crm_instance_url(crm)
        response = self.nc_client.get(instance_url)
        if not response.ok:
            raise SugarCRMBackendError(
                'Cannot get details of CRMs instance: response code - %s, response content: %s.'
                'Request URL: %s' % (response.status_code, response.content, response.request.url))
        return response.json()

    def get_crm_template_group_result_details(self, crm):
        """ Get details of CRMs template group provision result """
        template_group_result_url = crm.backend_id
        response = self.nc_client.get(template_group_result_url)
        if not response.ok:
            raise SugarCRMBackendError(
                'Cannot get CRMs provision result details: response code - %s, response content: %s.'
                'Request URL: %s' % (response.status_code, response.content, response.request.url))
        return response.json()

    def get_crm_instance_url(self, crm):
        if not crm.backend_id:
            raise SugarCRMBackendError('Cannot get instance URL for CRM without backend id')
        template_group_result_url = crm.backend_id
        response = self.nc_client.get(template_group_result_url)
        if not response.ok:
            raise SugarCRMBackendError(
                'Cannot get details of CRMs template group result: response code - %s, response content: %s.'
                'Request URL: %s' % (response.status_code, response.content, response.request.url))
        return response.json()['provisioned_resources']['OpenStack.Instance']

    def create_user(self, user_name, password, last_name, **kwargs):
        encoded_password = md5.new(password).hexdigest()
        try:
            user = self.sugar_client.create_user(
                user_name=user_name, user_hash=encoded_password, last_name=last_name, **kwargs)
        except (requests.exceptions.RequestException, sugarcrm.SugarError) as e:
            raise SugarCRMBackendError(
                'Cannot create user %s on CRM "%s". Error: %s' % (user_name, self.crm.name, self.sugar_client.url, e))

        logger.info('Successfully created user "%s" for CRM "%s"', user_name, self.crm.name)
        return user

    def delete_user(self, user):
        try:
            self.sugar_client.delete_user(user)
        except (requests.exceptions.RequestException, sugarcrm.SugarError) as e:
            raise SugarCRMBackendError(
                'Cannot delete user with id %s from CRM "%s". Error: %s' % (user.id, self.crm.name, e))

        logger.info('Successfully deleted user with id %s on CRM "%s"', user.id, self.crm.name)

    def get_user(self, user_id):
        try:
            return self.sugar_client.get_user(user_id)
        except (requests.exceptions.RequestException, sugarcrm.SugarError) as e:
            raise SugarCRMBackendError(
                'Cannot get user with id %s from CRM "%s". Error: %s' % (user_id, self.crm.name, e))

    def list_users(self):
        try:
            return self.sugar_client.list_users()
        except (requests.exceptions.RequestException, sugarcrm.SugarError) as e:
            raise SugarCRMBackendError('Cannot get users from CRM "%s". Error: %s' % (self.crm.name, e))


class SugarCRMDummyBackend(SugarCRMBaseBackend):
    pass
