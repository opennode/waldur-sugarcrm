from __future__ import unicode_literals

from django.db import models

from nodeconductor.core import utils as core_utils
from nodeconductor.cost_tracking.models import PayableMixin
from nodeconductor.quotas.fields import QuotaField, LimitAggregatorQuotaField, CounterQuotaField
from nodeconductor.quotas.models import QuotaModelMixin
from nodeconductor.structure import models as structure_models


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
        user_limit_count = LimitAggregatorQuotaField(
            default_limit=50,
            get_children=lambda spl: CRM.objects.filter(service_project_link=spl),
            child_quota_name='user_count',
        )
        crm_count = CounterQuotaField(
            target_models=lambda: [CRM],
            path_to_scope='service_project_link',
            default_limit=-1,
        )

    class Meta(structure_models.ServiceProjectLink.Meta):
        verbose_name = 'SugarCRM service project link'
        verbose_name_plural = 'SugarCRM service project links'

    @classmethod
    def get_url_name(cls):
        return 'sugarcrm-spl'


class CRM(QuotaModelMixin, structure_models.PublishableResource, structure_models.ApplicationMixin,
          PayableMixin):
    service_project_link = models.ForeignKey(
        SugarCRMServiceProjectLink, related_name='crms', on_delete=models.PROTECT)

    api_url = models.CharField(max_length=127, help_text='CRMs OpenStack instance access URL.')
    admin_username = models.CharField(max_length=60)
    admin_password = models.CharField(max_length=255)
    instance_url = models.URLField(blank=True, help_text='CRMs OpenStack instance URL in NC.')

    class Quotas(QuotaModelMixin.Quotas):
        user_count = QuotaField(default_limit=0)

    class Meta:
        verbose_name = 'CRM'
        verbose_name_plural = 'CRMs'

    @classmethod
    def get_url_name(cls):
        return 'sugarcrm-crms'

    @property
    def full_name(self):
        return 'SugarCRM Instance %s' % self.name

    def get_backend(self):
        from .backend import SugarCRMBackend
        return SugarCRMBackend(settings=self.service_project_link.service.settings, crm=self)

    def get_instance(self):
        """ Restore instance from URL """
        return core_utils.instance_from_url(self.instance_url)

    def as_dict(self):
        """ Represent instance as dict with all necessary attributes """
        return {
            'name': self.name,
            'description': self.description,
            'service_project_link': self.service_project_link.pk,
            'admin_username': self.admin_username,
            'admin_password': self.admin_password,
            'tags': [tag.name for tag in self.tags.all()],
        }
