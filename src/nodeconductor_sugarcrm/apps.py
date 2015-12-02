from django.apps import AppConfig
from django.db.models import signals

from nodeconductor.cost_tracking import CostTrackingRegister
from nodeconductor.quotas.models import Quota
from nodeconductor.structure import SupportedServices
from nodeconductor.template import TemplateRegistry


class SugarCRMConfig(AppConfig):
    name = 'nodeconductor_sugarcrm'
    verbose_name = "NodeConductor SugarCRM"
    service_name = 'SugarCRM'

    def ready(self):
        # structure
        from .backend import SugarCRMBackend
        SupportedServices.register_backend(SugarCRMBackend)

        # cost tracking
        from .cost_tracking import SugarCRMCostTrackingBackend
        CostTrackingRegister.register(self.label, SugarCRMCostTrackingBackend)

        # template
        from .template import CRMProvisionTemplateForm
        TemplateRegistry.register(CRMProvisionTemplateForm)

        from . import handlers, models

        signals.post_save.connect(
            handlers.update_user_limit_count_quota_on_crm_quota_change,
            sender=Quota,
            dispatch_uid='nodeconductor_sugarcrm.handlers.update_user_limit_count_quota_on_crm_quota_change',
        )

        signals.pre_delete.connect(
            handlers.update_user_limit_count_quota_on_crm_deletion,
            sender=models.CRM,
            dispatch_uid='nodeconductor_sugarcrm.handlers.update_user_limit_count_quota_on_crm_deletion'
        )
