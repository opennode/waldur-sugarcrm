from django.apps import AppConfig

from nodeconductor.cost_tracking import CostTrackingRegister
from nodeconductor.structure import SupportedServices


class SugarCRMConfig(AppConfig):
    name = 'nodeconductor_sugarcrm'
    verbose_name = "NodeConductor SugarCRM"

    def ready(self):
        SugarCRMService = self.get_model('SugarCRMService')

        from .backend import SugarCRMBackend
        from .cost_tracking import SugarCRMCostTrackingBackend
        SupportedServices.register_backend(SugarCRMService, SugarCRMBackend)
        CostTrackingRegister.register(self.label, SugarCRMCostTrackingBackend)
