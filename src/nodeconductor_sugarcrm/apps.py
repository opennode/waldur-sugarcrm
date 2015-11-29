from django.apps import AppConfig

from nodeconductor.cost_tracking import CostTrackingRegister
from nodeconductor.structure import SupportedServices
from nodeconductor.template import TemplateRegistry


class SugarCRMConfig(AppConfig):
    name = 'nodeconductor_sugarcrm'
    verbose_name = "NodeConductor SugarCRM"

    def ready(self):
        SugarCRMService = self.get_model('SugarCRMService')

        # structure
        from .backend import SugarCRMBackend
        SupportedServices.register_backend(SugarCRMService, SugarCRMBackend)

        # cost tracking
        from .cost_tracking import SugarCRMCostTrackingBackend
        CostTrackingRegister.register(self.label, SugarCRMCostTrackingBackend)

        # template
        from .template import CRMProvisionTemplateForm
        TemplateRegistry.register(CRMProvisionTemplateForm)
