from django import forms

from rest_framework import serializers

from nodeconductor.structure import models as structure_models
from nodeconductor.template.forms import TemplateForm
from nodeconductor.template.serializers import BaseTemplateSerializer
from nodeconductor_sugarcrm import models


# TODO: Filter service settings of defined type
class CRMProvisionTemplateForm(TemplateForm):
    service_settings = forms.ModelChoiceField(
        label="SugarCRM service settings",
        queryset=structure_models.ServiceSettings.objects.all(),
        required=False)

    user_count = forms.IntegerField(required=False)

    class Meta(TemplateForm.Meta):
        fields = TemplateForm.Meta.fields + ('service_settings', 'user_count')

    class Serializer(BaseTemplateSerializer):
        service_settings = serializers.HyperlinkedRelatedField(
            view_name='servicesettings-detail',
            queryset=structure_models.ServiceSettings.objects.all(),
            lookup_field='uuid',
            required=False,
        )
        user_count = serializers.IntegerField(required=False)

    @classmethod
    def get_serializer_class(cls):
        return cls.Serializer

    @classmethod
    def get_resource_model(cls):
        return models.CRM
