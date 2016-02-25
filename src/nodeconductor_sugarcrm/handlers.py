from . import models, log


event_logger = log.event_logger


def update_user_limit_count_quota_on_crm_quota_change(sender, instance, created, **kwargs):
    quota = instance
    if not isinstance(quota.scope, models.CRM) or quota.name != models.CRM.Quotas.user_count.name:
        return
    crm = quota.scope

    if created:
        crm.service_project_link.add_quota_usage(crm.service_project_link.Quotas.user_limit_count, quota.limit)
    elif quota.tracker.has_changed('limit'):
        crm.service_project_link.add_quota_usage(
            crm.service_project_link.Quotas.user_limit_count, quota.limit - quota.tracker.previous('limit'))


def update_user_limit_count_quota_on_crm_deletion(sender, instance, **kwargs):
    crm = instance
    quota = crm.quotas.get(name=crm.Quotas.user_count)
    crm.service_project_link.add_quota_usage(crm.service_project_link.Quotas.user_limit_count, -quota.limit)


# logging

def log_user_post_save(sender, user, crm, created=False, **kwargs):
    if created:
        event_logger.sugarcrm_user.info(
            'User {user_name} has been created in CRM {crm_name}.',
            event_type='sugarcrm_user_creation_succeeded',
            event_context={
                'user_name': user.user_name,
                'crm': crm,
            })
    else:
        event_logger.sugarcrm_user.info(
            'User {user_name} has been updated in CRM {crm_name}.',
            event_type='sugarcrm_user_update_succeeded',
            event_context={
                'user_name': user.user_name,
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
