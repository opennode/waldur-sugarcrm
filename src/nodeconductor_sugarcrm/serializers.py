import re

from rest_framework import serializers
from rest_framework.reverse import reverse

from nodeconductor.core import serializers as core_serializers
from nodeconductor.quotas import serializers as quotas_serializers
from nodeconductor.structure import serializers as structure_serializers

from . import models


class ServiceSerializer(structure_serializers.BaseServiceSerializer):

    SERVICE_ACCOUNT_FIELDS = {
        'backend_url': 'URL of template group that describes OpenStack instance provision with default parameters'
                       '(required, e.g.: http://example.com/api/template-groups/16c7675752244f5d9e870a2cb0cfeb02/)',
        'username': 'NodeConductor user username (e.g. Username)',
        'password': 'NodeConductor user password (e.g. Password)',
    }
    SERVICE_ACCOUNT_EXTRA_FIELDS = {
        'license_code': 'License code that will be used for SugarCRM activation',
        'user_data': 'User data that will be passed to CRMs OpenStack instance on creation'
                     'Word {password} will be replaced with auto-generated admin password',
        'protocol': 'CRMs access protocol',
        'phone_regex': 'RegEx for phone validation',
        'sms_email_from': 'Name of SMS email sender',
        'sms_email_rcpt': 'Name of SMS email recipient',
    }

    class Meta(structure_serializers.BaseServiceSerializer.Meta):
        model = models.SugarCRMService
        view_name = 'sugarcrm-detail'
        required_fields = 'license_code',


class ServiceProjectLinkSerializer(structure_serializers.BaseServiceProjectLinkSerializer):
    quotas = quotas_serializers.BasicQuotaSerializer(many=True, read_only=True)

    class Meta(structure_serializers.BaseServiceProjectLinkSerializer.Meta):
        model = models.SugarCRMServiceProjectLink
        view_name = 'sugarcrm-spl-detail'
        extra_kwargs = {
            'service': {'lookup_field': 'uuid', 'view_name': 'sugarcrm-detail'},
        }
        fields = structure_serializers.BaseServiceProjectLinkSerializer.Meta.fields + ('quotas',)


class CRMSerializer(structure_serializers.PublishableResourceSerializer):
    service = serializers.HyperlinkedRelatedField(
        source='service_project_link.service',
        view_name='sugarcrm-detail',
        read_only=True,
        lookup_field='uuid')

    service_project_link = serializers.HyperlinkedRelatedField(
        view_name='sugarcrm-spl-detail',
        queryset=models.SugarCRMServiceProjectLink.objects.all())

    user_count = serializers.IntegerField(
        min_value=0, default=models.CRM.Quotas.user_count.default_limit, write_only=True)
    quotas = quotas_serializers.BasicQuotaSerializer(many=True, read_only=True)

    class Meta(structure_serializers.PublishableResourceSerializer.Meta):
        model = models.CRM
        view_name = 'sugarcrm-crms-detail'
        fields = structure_serializers.PublishableResourceSerializer.Meta.fields + (
            'api_url', 'user_count', 'quotas', 'instance_url')
        read_only_fields = structure_serializers.PublishableResourceSerializer.Meta.read_only_fields + (
            'api_url', 'instance_url')
        protected_fields = structure_serializers.PublishableResourceSerializer.Meta.protected_fields + ('user_count', )

    def get_fields(self):
        fields = super(CRMSerializer, self).get_fields()
        if 'request' in self.context and not self.context['request'].user.is_staff:
            fields.pop('instance_url', None)
        return fields

    def validate(self, attrs):
        if not self.instance:
            # quota check on creation. update is done through /quotas endpoint
            spl = attrs['service_project_link']
            quota = spl.quotas.get(name=models.SugarCRMServiceProjectLink.Quotas.user_limit_count)
            # usage delta for the SPL quota is equal to the limit of the resource
            delta = attrs['user_count']
            if quota.is_exceeded(delta=delta):
                raise serializers.ValidationError(
                    'Service project link users count quota is over limit (limit: %s, required: %s)' %
                    (quota.limit, quota.usage + delta))
        return attrs


class CRMUserSerializer(core_serializers.AugmentedSerializerMixin, serializers.Serializer):

    url = serializers.SerializerMethodField()
    uuid = serializers.CharField(read_only=True, source='id')
    user_name = serializers.CharField(max_length=60)
    status = serializers.CharField(max_length=30, required=False)
    last_name = serializers.CharField(max_length=30)
    first_name = serializers.CharField(max_length=30, required=False)
    email = serializers.CharField(source='email1', max_length=255, required=False)
    phone = serializers.CharField(source='phone_mobile', max_length=30, required=False, allow_blank=True)
    notify = serializers.BooleanField(write_only=True, required=False)

    class Meta(object):
        protected_fields = ['user_name', 'notify']

    def get_fields(self):
        fields = super(CRMUserSerializer, self).get_fields()
        # mark fields as not required on update
        if self.instance is not None:
            for field in fields.values():
                field.required = False
        return fields

    def get_url(self, obj):
        crm = self.context['crm']
        request = self.context['request']
        return reverse('sugarcrm-users-detail', kwargs={'crm_uuid': crm.uuid.hex, 'pk': obj.id}, request=request)

    def validate_user_name(self, value):
        crm = self.context['crm']
        users = crm.get_backend().list_users()
        exist_user_names = [u.user_name for u in users]
        if value in exist_user_names:
            raise serializers.ValidationError('User with such name already exists.')
        return value

    def validate(self, attrs):
        attrs = super(CRMUserSerializer, self).validate(attrs)
        if not self.instance:
            crm = self.context['crm']
            user_count_quota = crm.quotas.get(name=crm.Quotas.user_count)
            if user_count_quota.is_exceeded(delta=1):
                raise serializers.ValidationError(
                    'User count quota is over limit (users count: %s, max users count: %s).' %
                    (user_count_quota.usage, user_count_quota.limit))

        crm = self.context['crm']
        phone = attrs.get('phone_mobile')
        if phone:
            settings = crm.service_project_link.service.settings
            phone_regex = settings.get_option('phone_regex')
            if phone_regex and not re.search(phone_regex, phone):
                raise serializers.ValidationError({'phone': "Invalid phone number."})

        if attrs.get('notify', False) and not phone:
            raise serializers.ValidationError({'phone': "Missed phone number for notification."})

        return attrs


class UserPasswordSerializer(serializers.Serializer):
    notify = serializers.BooleanField(required=False)

    def validate(self, attrs):
        attrs = super(UserPasswordSerializer, self).validate(attrs)
        user = self.context['user']

        if attrs.get('notify', False) and not user.phone_mobile:
            raise serializers.ValidationError('User must have phone number for sending notifications.')

        return attrs
