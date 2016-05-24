from . import log


event_logger = log.event_logger


# logging
def log_user_post_save(sender, old_user, new_user, crm, created=False, **kwargs):
    if created:
        event_logger.sugarcrm_user.info(
            'User {user_name} has been created in CRM {crm_name}.',
            event_type='sugarcrm_user_creation_succeeded',
            event_context={
                'user_name': new_user.user_name,
                'crm': crm,
            })
    else:
        # check if activation has been requested
        if old_user.status != new_user.status:
            if new_user.status == 'Active':
                event_logger.sugarcrm_user.info(
                    'User {user_name} has been activated in CRM {crm_name}.',
                    event_type='sugarcrm_user_activation_succeeded',
                    event_context={
                        'user_name': new_user.user_name,
                        'crm': crm,
                    })
            elif new_user.status == 'Inactive':
                event_logger.sugarcrm_user.info(
                    'User {user_name} has been deactivated in CRM {crm_name}.',
                    event_type='sugarcrm_user_deactivation_succeeded',
                    event_context={
                        'user_name': new_user.user_name,
                        'crm': crm,
                    })

        event_logger.sugarcrm_user.info(
            'User {user_name} has been updated in CRM {crm_name}.',
            event_type='sugarcrm_user_update_succeeded',
            event_context={
                'user_name': new_user.user_name,
                'crm': crm,
            })


def log_user_post_delete(sender, user, crm, **kwargs):
    event_logger.sugarcrm_user.info(
        'User {user_name} has been deleted from CRM {crm_name}.',
        event_type='sugarcrm_user_deletion_succeeded',
        event_context={
            'user_name': user.user_name,
            'crm': crm,
        })
