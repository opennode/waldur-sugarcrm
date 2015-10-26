from django.apps import AppConfig

from nodeconductor.structure import SupportedServices


class SugarCRMConfig(AppConfig):
    name = 'nodeconductor_sugarcrm'
    verbose_name = "NodeConductor SugarCRM"

    def ready(self):
        SugarCRMService = self.get_model('SugarCRMService')

        from .backend import SugarCRMBackend
        SupportedServices.register_backend(SugarCRMService, SugarCRMBackend)
