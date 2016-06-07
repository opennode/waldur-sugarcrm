import logging
import md5
import urlparse

from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import Resolver404
from django.utils import six
import requests
from rest_framework.reverse import reverse
import sugarcrm

from nodeconductor.core.tasks import send_task
from nodeconductor.core.utils import pwgen
from nodeconductor.structure import ServiceBackend, ServiceBackendError

from . import models


logger = logging.getLogger(__name__)


class SugarCRMBackendError(ServiceBackendError):
    pass


class SugarCRMBaseBackend(ServiceBackend):

    def __init__(self, settings, crm=None):
        self.settings = settings
        self.crm = crm

    def provision(self, crm, user_count):
        crm.set_quota_limit(crm.Quotas.user_count, user_count)
        send_task('sugarcrm', 'provision_crm')(
            crm.uuid.hex,
        )

    def destroy(self, crm, force=False):
        # CRM cannot be stopped by user - so we need to stop it before deletion on destroy
        crm.state = crm.States.STOPPING_SCHEDULED
        crm.save()
        send_task('sugarcrm', 'stop_and_destroy_crm')(
            crm.uuid.hex,
            force=force,
        )

    def sync(self):
        pass


class SugarCRMBackend(SugarCRMBaseBackend):
    """ Sugar CRM backend methods

    Backend uses two clients for operations:
    1. NodeCondcutor OpenStack client uses to NC OpenStack application endpoints for operations with SugarCRM VM.
    2. SugarCRM client interacts with SugarCRM API.
    """

    DEFAULTS = {
        'user_data': "#cloud-config:\nruncmd:\n  - [ bootstrap, -p, {password}, -k, {license_code}, -v]",
        'protocol': "http",
    }

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

        class UserStatuses(object):
            ACTIVE = 'Active'
            INACTIVE = 'Inactive'
            RESERVED = 'Reserved'

        def __init__(self, url, username, password):
            self.v4_url = url + '/service/v4/rest.php'
            self.v10_url = url + '/rest/v10/'
            self.username = username
            self.password = password
            self.v4_session = sugarcrm.Session(self.v4_url, username, password)

        def execute_v10_request(self, method, url, json_data):
            method = getattr(requests, method.lower())
            if not hasattr(self, '_v10_headers'):
                self._v10_headers = self._get_v10_headers()
            return method(url, json=json_data, headers=self._v10_headers)

        def _get_v10_headers(self):
            auth_url = self.v10_url + 'oauth2/token/'
            json_data = {
                'client_id': 'sugar',
                'client_secret': '',
                'grant_type': 'password',
                'password': self.password,
                'platform': 'base',
                'username': self.username,
            }
            response = requests.post(auth_url, json=json_data).json()
            return {'oauth-token': response['access_token']}

        def create_user(self, **kwargs):
            user = sugarcrm.User()
            for key, value in kwargs.items():
                setattr(user, key, value)
            return self.v4_session.set_entry(user)

        def update_user(self, user, **kwargs):
            # It is possible to update user status only with v10 API
            if 'status' in kwargs:
                url = self.v10_url + 'Users/%s/' % user.id
                self.execute_v10_request('PUT', url, json_data={'status': kwargs['status']})
            for key, value in kwargs.items():
                setattr(user, key, value)
            return self.v4_session.set_entry(user)

        def get_user(self, user_id):
            return self.v4_session.get_entry('Users', user_id)

        def list_users(self, **kwargs):
            # admin users should not be visible
            user_query = sugarcrm.User(is_admin='0')
            user_count = self.v4_session.get_entries_count(user_query)

            step = 100
            users = []
            for offset in range(0, user_count, step):
                users += self.v4_session.get_entry_list(user_query, max_results=step, offset=offset)
            # do not show users that are reserved by sugarcrm:
            users = [user for user in users if user.status != self.UserStatuses.RESERVED]
            # XXX: SugarCRM cannot filter 2 arguments together - its easier to filter users here.
            return [user for user in users if all(getattr(user, k) == v for k, v in kwargs.items())]

        def delete_user(self, user):
            user.deleted = 1
            self.v4_session.set_entry(user)

    def __init__(self, *args, **kwargs):
        super(SugarCRMBackend, self).__init__(*args, **kwargs)

        self.template_url = self.settings.backend_url
        self.nc_client = self.NodeConductorOpenStackClient(
            self.template_url, self.settings.username, self.settings.password)

    @property
    def sugar_client(self):
        if hasattr(self, '_sugar_client'):
            return self._sugar_client
        if self.crm is None:
            raise SugarCRMBackendError('It is impossible to use sugar client if CRM is not specified for backend.')
        try:
            self._sugar_client = self.SugarCRMClient(self.crm.api_url, self.crm.admin_username, self.crm.admin_password)
        except KeyError:
            raise SugarCRMBackendError('Cannot connect to CRM backend.')
        return self._sugar_client

    def schedule_crm_instance_provision(self, crm):
        # prepare data for template group provisioning
        user_data = self.settings.get_option('user_data')
        admin_username = self.CRM_ADMIN_NAME
        admin_password = pwgen()
        user_data = user_data.format(
            password=admin_password, license_code=self.settings.get_option('license_code'))

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
        crm.backend_id = response.json()['url']
        crm.instance_url = response.json()['provisioned_resources']['OpenStack.Instance']
        crm.save()

        logger.info('Successfully scheduled instance provision for CRM "%s"', crm.name)

    def schedule_crm_instance_stopping(self, crm):
        response = self.nc_client.post(crm.instance_url + 'stop/')
        if not response.ok:
            raise SugarCRMBackendError(
                'Cannot stop OpenStack instance for CRM "%s": response code - %s, response content: %s.'
                'Request URL: %s, request body: %s' %
                (crm.name, response.status_code, response.content, response.request.url, response.request.body))

        logger.info('Successfully scheduled instance stopping for CRM "%s"', crm.name)

    def schedule_crm_instance_deletion(self, crm):
        response = self.nc_client.delete(crm.instance_url)
        if not response.ok:
            raise SugarCRMBackendError(
                'Cannot delete OpenStack instance for CRM "%s": response code - %s, response content: %s.'
                'Request URL: %s, request body: %s' %
                (crm.name, response.status_code, response.content, response.request.url, response.request.body))

        logger.info('Successfully scheduled instance deletion for CRM "%s"', crm.name)

    def pull_crm_sla(self, crm):
        """ Copy OpenStack instance SLA and events as CRM events """
        try:
            instance = crm.get_instance()
        except (Resolver404, ObjectDoesNotExist) as e:
            crm.error_message = 'Cannot get instance for CRM %s (PK: %s). Error: %s' % (crm.name, crm.pk, e)
            crm.set_erred()
            crm.save()
            logger.error(crm.error_message)
            six.reraise(SugarCRMBackendError, e)
        else:
            for item in instance.sla_items.all():
                crm.sla_items.update_or_create(
                    period=item.period,
                    defaults={'value': item.value, 'agreed_value': item.agreed_value},
                )
            for state_transition in instance.state_items.all():
                crm.state_items.update_or_create(
                    period=state_transition.period,
                    timestamp=state_transition.timestamp,
                    defaults={'state': state_transition.state},
                )

        logger.info('Successfully pulled SLA for CRM "%s"', crm.name)

    def get_crm_instance_details(self, crm):
        """ Get details of instance that corresponds given CRM """
        response = self.nc_client.get(crm.instance_url)
        if not response.ok:
            raise SugarCRMBackendError(
                'Cannot get details of CRMs instance: response code - %s, response content: %s.'
                'Request URL: %s' % (response.status_code, response.content, response.request.url))
        return response.json()

    def get_crm_template_group_result_details(self, crm):
        """ Get details of CRMs template group provision result """
        if not crm.backend_id:
            raise SugarCRMBackendError('Cannot get instance URL for CRM without backend id')
        template_group_result_url = crm.backend_id
        response = self.nc_client.get(template_group_result_url)
        if not response.ok:
            raise SugarCRMBackendError(
                'Cannot get CRMs provision result details: response code - %s, response content: %s.'
                'Request URL: %s' % (response.status_code, response.content, response.request.url))
        return response.json()

    def create_user(self, user_name, password, last_name, **kwargs):
        encoded_password = self._encode_password(password)
        try:
            user = self.sugar_client.create_user(
                user_name=user_name, user_hash=encoded_password, last_name=last_name, **kwargs)
        except (requests.exceptions.RequestException, sugarcrm.SugarError) as e:
            raise SugarCRMBackendError(
                'Cannot create user %s on CRM "%s". Error: %s' % (user_name, self.crm.name, e))

        self.crm.add_quota_usage(self.crm.Quotas.user_count, 1)
        logger.info('Successfully created user "%s" for CRM "%s"', user_name, self.crm.name)
        return user

    def update_user(self, user, **kwargs):
        if 'password' in kwargs:
            kwargs['user_hash'] = self._encode_password(kwargs.pop('password'))
        try:
            user = self.sugar_client.update_user(user, **kwargs)
        except (requests.exceptions.RequestException, sugarcrm.SugarError) as e:
            raise SugarCRMBackendError(
                'Cannot update user %s on CRM "%s". Error: %s' % (user.user_name, self.crm.name, e))

        logger.info('Successfully updated user "%s" for CRM "%s"', user.user_name, self.crm.name)
        return user

    def _encode_password(self, password):
        return md5.new(password).hexdigest()

    def delete_user(self, user):
        try:
            self.sugar_client.delete_user(user)
        except (requests.exceptions.RequestException, sugarcrm.SugarError) as e:
            raise SugarCRMBackendError(
                'Cannot delete user with id %s from CRM "%s". Error: %s' % (user.id, self.crm.name, e))

        self.crm.add_quota_usage(self.crm.Quotas.user_count, -1)
        logger.info('Successfully deleted user with id %s on CRM "%s"', user.id, self.crm.name)

    def get_user(self, user_id):
        try:
            return self.sugar_client.get_user(user_id)
        except (requests.exceptions.RequestException, sugarcrm.SugarError) as e:
            raise SugarCRMBackendError(
                'Cannot get user with id %s from CRM "%s". Error: %s' % (user_id, self.crm.name, e))

    def list_users(self, **kwargs):
        try:
            return self.sugar_client.list_users(**kwargs)
        except (requests.exceptions.RequestException, sugarcrm.SugarError) as e:
            raise SugarCRMBackendError('Cannot get users from CRM "%s". Error: %s' % (self.crm.name, e))

    def sync_user_quota(self):
        """ Sync CRM quotas with backend """
        active_users = self.list_users(status=self.SugarCRMClient.UserStatuses.ACTIVE)
        self.crm.set_quota_usage(self.crm.Quotas.user_count, len(active_users))

    def get_stats(self):
        links = models.CRM.objects.filter(
            service_project_link__service__settings=self.settings)
        quota_values = models.CRM.get_sum_of_quotas_as_dict(links, quota_names=('user_count',))
        stats = {
            'user_count_quota': quota_values.get('user_count', -1.0),
            'user_count_usage': quota_values.get('user_count_usage', 0.0)
        }

        try:
            quota = self.settings.quotas.get(name='sugarcrm_user_count')
            stats['user_count'] = quota.limit
        except ObjectDoesNotExist:
            stats['user_count'] = -1.0
        return stats
