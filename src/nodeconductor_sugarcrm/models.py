from django.db import models

from nodeconductor.billing.models import PaidResource
from nodeconductor.cost_tracking import CostConstants
from nodeconductor.structure import ServiceBackend, models as structure_models

from .backend import SugarCRMBackend


class SugarCRMService(structure_models.Service):
    projects = models.ManyToManyField(
        structure_models.Project, related_name='sugarcrm_services', through='SugarCRMServiceProjectLink')

    @classmethod
    def get_url_name(cls):
        return 'sugarcrm'


class SugarCRMServiceProjectLink(structure_models.ServiceProjectLink):
    service = models.ForeignKey(SugarCRMService)

    class Meta:
        unique_together = ('service', 'project')

    @classmethod
    def get_url_name(cls):
        return 'sugarcrm-spl'


class CRM(PaidResource, structure_models.Resource):
    service_project_link = models.ForeignKey(
        SugarCRMServiceProjectLink, related_name='crms', on_delete=models.PROTECT)

    api_url = models.CharField(max_length=127)
    admin_username = models.CharField(max_length=60)
    admin_password = models.CharField(max_length=255)

    def get_usage_state(self):
        backend = self.get_backend()
        details = backend.get_crm_instance_details(self)
        return {
            CostConstants.PriceItem.USAGE: 1,
            CostConstants.PriceItem.STORAGE: ServiceBackend.mb2gb(details['disk']),
        }

    @classmethod
    def get_url_name(cls):
        return 'sugarcrm-crms'

    def get_backend(self):
        return SugarCRMBackend(settings=self.service_project_link.service.settings, crm=self)
