from . import models


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
