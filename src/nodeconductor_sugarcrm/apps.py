from django.apps import AppConfig

from nodeconductor.cost_tracking import CostTrackingRegister
from nodeconductor.structure import SupportedServices


class SugarCRMConfig(AppConfig):
    name = 'nodeconductor_sugarcrm'
    verbose_name = "NodeConductor SugarCRM"
    service_name = 'SugarCRM'

    def ready(self):
        from .backend import SugarCRMBackend
        from .cost_tracking import SugarCRMCostTrackingBackend
        SupportedServices.register_backend(SugarCRMBackend)
        CostTrackingRegister.register(self.label, SugarCRMCostTrackingBackend)
