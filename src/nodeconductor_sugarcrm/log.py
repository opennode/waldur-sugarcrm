from nodeconductor.logging.log import EventLogger, event_logger

from .models import CRM


class SugarCRMUserEventLogger(EventLogger):
    user_name = basestring
    crm = CRM

    class Meta:
        event_types = (
            'sugarcrm_user_creation_succeeded',
            'sugarcrm_user_update_succeeded',
            'sugarcrm_user_deletion_succeeded',
        )


event_logger.register('sugarcrm_user', SugarCRMUserEventLogger)
