from django import forms

from rest_framework import serializers

from nodeconductor.structure import models as structure_models
from nodeconductor.template.forms import ResourceTemplateForm
from nodeconductor.template.serializers import BaseResourceTemplateSerializer
from nodeconductor_sugarcrm import models


# TODO: Filter service settings of defined type
class CRMProvisionTemplateForm(ResourceTemplateForm):
    service_settings = forms.ModelChoiceField(
        label="SugarCRM service settings",
        queryset=structure_models.ServiceSettings.objects.all(),
        required=False)

    user_count = forms.IntegerField(required=False)

    class Meta(ResourceTemplateForm.Meta):
        fields = ResourceTemplateForm.Meta.fields + ('service_settings', 'user_count')

    class Serializer(BaseResourceTemplateSerializer):
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
    def get_model(cls):
        return models.CRM
