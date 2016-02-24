from __future__ import unicode_literals

from django.db import models

from nodeconductor.quotas.fields import QuotaField
from nodeconductor.quotas.models import QuotaModelMixin
from nodeconductor.structure import models as structure_models

from .backend import SugarCRMBackend


class SugarCRMService(structure_models.Service):
    projects = models.ManyToManyField(
        structure_models.Project, related_name='sugarcrm_services', through='SugarCRMServiceProjectLink')

    class Meta:
        verbose_name = 'SugarCRM service'
        verbose_name_plural = 'SugarCRM services'
        unique_together = ('customer', 'settings')

    @classmethod
    def get_url_name(cls):
        return 'sugarcrm'


class SugarCRMServiceProjectLink(structure_models.ServiceProjectLink):
    service = models.ForeignKey(SugarCRMService)

    class Quotas(QuotaModelMixin.Quotas):
        user_limit_count = QuotaField(default_limit=50)

    class Meta(structure_models.ServiceProjectLink.Meta):
        verbose_name = 'SugarCRM service project link'
        verbose_name_plural = 'SugarCRM service project links'

    @classmethod
    def get_url_name(cls):
        return 'sugarcrm-spl'


class CRM(QuotaModelMixin, structure_models.Resource, structure_models.PaidResource):
    service_project_link = models.ForeignKey(
        SugarCRMServiceProjectLink, related_name='crms', on_delete=models.PROTECT)

    api_url = models.CharField(max_length=127, help_text='CRMs OpenStack instance URL')
    admin_username = models.CharField(max_length=60)
    admin_password = models.CharField(max_length=255)

    class Quotas(QuotaModelMixin.Quotas):
        user_count = QuotaField(default_limit=10)

    class Meta:
        verbose_name = 'CRM'
        verbose_name_plural = 'CRMs'

    @classmethod
    def get_url_name(cls):
        return 'sugarcrm-crms'

    def get_backend(self):
        return SugarCRMBackend(settings=self.service_project_link.service.settings, crm=self)
