from django.db import models

from nodeconductor.structure import models as structure_models


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


class CRM(structure_models.Resource):
    service_project_link = models.ForeignKey(
        SugarCRMServiceProjectLink, related_name='crms', on_delete=models.PROTECT)

    api_url = models.CharField(max_length=127)
    admin_username = models.CharField(max_length=60)
    admin_password = models.CharField(max_length=255)

    @classmethod
    def get_url_name(cls):
        return 'sugarcrm-crms'
