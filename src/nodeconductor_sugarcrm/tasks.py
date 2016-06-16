import logging
import sys

from celery import shared_task, chain
from django.utils import six, timezone

from nodeconductor.core import utils as core_utils
from nodeconductor.core.tasks import save_error_message, transition, retry_if_false, BackendMethodTask

from .backend import SugarCRMBackendError
from .models import CRM


logger = logging.getLogger(__name__)


@shared_task(name='nodeconductor.sugarcrm.provision_crm')
def provision_crm(crm_uuid):
    chain(
        schedule_crm_instance_provision.si(crm_uuid),
        wait_for_crm_template_group_provision.si(crm_uuid),
        init_crm_api_url.si(crm_uuid),
        init_crm_quotas.si(crm_uuid),
    ).apply_async(
        link=set_online.si(crm_uuid),
        link_error=set_erred.si(crm_uuid)
    )


@shared_task(name='nodeconductor.sugarcrm.stop_and_destroy_crm')
def stop_and_destroy_crm(crm_uuid, force=False):
    if not force:
        error_callback = set_erred.si(crm_uuid)
    else:
        error_callback = force_delete.si(crm_uuid)
    chain(
        schedule_crm_instance_stopping.si(crm_uuid),
        wait_for_crm_instance_state.si(crm_uuid, state='Offline'),
        set_offline.si(crm_uuid),
        schedule_deletion.si(crm_uuid),
        schedule_crm_instance_deletion.si(crm_uuid),
    ).apply_async(
        link=delete.si(crm_uuid),
        link_error=error_callback,
    )


@shared_task
@transition(CRM, 'begin_provisioning')
@save_error_message
def schedule_crm_instance_provision(crm_uuid, transition_entity=None):
    crm = transition_entity
    backend = crm.get_backend()
    backend.schedule_crm_instance_provision(crm)


@shared_task
@transition(CRM, 'begin_stopping')
@save_error_message
def schedule_crm_instance_stopping(crm_uuid, transition_entity=None):
    crm = transition_entity
    backend = crm.get_backend()
    backend.schedule_crm_instance_stopping(crm)


@shared_task
@transition(CRM, 'begin_deleting')
@save_error_message
def schedule_crm_instance_deletion(crm_uuid, transition_entity=None):
    crm = transition_entity
    backend = crm.get_backend()
    backend.schedule_crm_instance_deletion(crm)


@shared_task(max_retries=120, default_retry_delay=20)
@retry_if_false
def wait_for_crm_instance_state(crm_uuid, state, erred_state='Erred'):
    crm = CRM.objects.get(uuid=crm_uuid)
    backend = crm.get_backend()
    details = backend.get_crm_instance_details(crm)
    current_state = details['state']
    logger.info('Checking state for CRM "%s" (UUID: %s) instance. Current value: %s.',
                crm.name, crm.uuid.hex, current_state)
    if current_state == erred_state:
        message = ('CRM "%s" (UUID: %s) instance with UUID %s become erred. Check OpenStack app logs '
                   'for more details.' % (crm.name, crm.uuid.hex, details['uuid']))
        crm.error_message = message
        crm.save()
        raise SugarCRMBackendError(message)
    return current_state == state


@shared_task(max_retries=120, default_retry_delay=20)
@retry_if_false
def wait_for_crm_template_group_provision(crm_uuid):
    crm = CRM.objects.get(uuid=crm_uuid)
    backend = crm.get_backend()
    details = backend.get_crm_template_group_result_details(crm)
    logger.info('Checking state of CRM "%s" (UUID: %s) provision result. Current state message: %s.',
                crm.name, crm.uuid.hex, details['state_message'])
    if details['is_erred']:
        message = ('CRM "%s" (UUID: %s) provision failed. result URL %s, message %s' % (
                   crm.name, crm.uuid.hex, details['url'], details['error_message']))
        crm.error_message = message
        crm.save()
        raise SugarCRMBackendError(message)
    return details['is_finished']


@shared_task
def init_crm_api_url(crm_uuid):
    """ Init CRM API URL """
    crm = CRM.objects.get(uuid=crm_uuid)
    settings = crm.service_project_link.service.settings
    backend = crm.get_backend()
    external_ips = backend.get_crm_instance_details(crm)['external_ips']
    if not external_ips:
        raise SugarCRMBackendError(
            'Cannot use OpenStack instance with name "%s" for CRM - it does not have external IP.' % crm.name)
    crm.api_url = '{protocol}://{external_ip}'.format(
        protocol=settings.get_option('protocol'),
        external_ip=external_ips[0])
    # we consider CRM as activated at this point
    crm.start_time = timezone.now()
    crm.save()


@shared_task(max_retries=30, default_retry_delay=10)
@retry_if_false
def init_crm_quotas(crm_uuid):
    """ Init CRM quotas """
    crm = CRM.objects.get(uuid=crm_uuid)
    backend = crm.get_backend()
    # It can take some time to initialize SugarCRM API, so we need to poll its API
    try:
        backend.sync_user_quota()
    except SugarCRMBackendError:
        return False
    else:
        return True


@shared_task
@transition(CRM, 'set_online')
def set_online(crm_uuid, transition_entity=None):
    pass


@shared_task
@transition(CRM, 'set_offline')
def set_offline(crm_uuid, transition_entity=None):
    pass


@shared_task
@transition(CRM, 'schedule_deletion')
def schedule_deletion(crm_uuid, transition_entity=None):
    pass


@shared_task
@transition(CRM, 'set_erred')
def set_erred(crm_uuid, transition_entity=None):
    pass


@shared_task
def delete(crm_uuid):
    CRM.objects.get(uuid=crm_uuid).delete()


@shared_task
def force_delete(crm_uuid):
    """ Schedule corresponding OpenStack instance deletion """
    crm = CRM.objects.get(uuid=crm_uuid)
    backend = crm.get_backend()
    try:
        backend.schedule_crm_instance_deletion(crm)
    except:
        six.reraise(*sys.exc_info())
    finally:
        crm.delete()


# celerybeat tasks:

@shared_task(name='nodeconductor.sugarcrm.sync_crms_quotas')
def sync_crms_quotas():
    """ Update quota usage from backend for all CRMs """
    for crm in CRM.objects.filter(state=CRM.States.ONLINE):
        sync_crm_quotas.delay(crm.uuid.hex)


@shared_task
def sync_crm_quotas(crm_uuid):
    crm = CRM.objects.get(uuid=crm_uuid)
    backend = crm.get_backend()
    backend.sync_user_quota()


@shared_task(name='nodeconductor.sugarcrm.pull_sla')
def pull_sla():
    """ Copy OpenStack instance SLA and events as CRM events """
    for crm in CRM.objects.filter(state=CRM.States.ONLINE):
        BackendMethodTask().delay(core_utils.serialize_instance(crm), 'pull_crm_sla')
