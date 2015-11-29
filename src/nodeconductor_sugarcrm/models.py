from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from nodeconductor.quotas.models import QuotaModelMixin
from nodeconductor.structure import models as structure_models

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


class CRM(QuotaModelMixin, structure_models.Resource, structure_models.PaidResource):
    service_project_link = models.ForeignKey(
        SugarCRMServiceProjectLink, related_name='crms', on_delete=models.PROTECT)

    size = models.PositiveIntegerField(
        default=2 * 1024, help_text='Size of CRMs OpenStack instance data volume in MiB',
        validators=[MinValueValidator(1024), MaxValueValidator(10 * 1024)])
    api_url = models.CharField(max_length=127, help_text='CRMs OpenStack instance URL')
    admin_username = models.CharField(max_length=60)
    admin_password = models.CharField(max_length=255)

    QUOTAS_NAMES = ['user_count']

    @classmethod
    def get_url_name(cls):
        return 'sugarcrm-crms'

    def get_backend(self):
        return SugarCRMBackend(settings=self.service_project_link.service.settings, crm=self)
