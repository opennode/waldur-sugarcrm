from rest_framework import serializers
from rest_framework.reverse import reverse

from nodeconductor.quotas import serializers as quotas_serializers
from nodeconductor.structure import serializers as structure_serializers
from . import models, backend


class ServiceSerializer(structure_serializers.BaseServiceSerializer):

    SERVICE_ACCOUNT_FIELDS = {
        'backend_url': 'URL of template group that describes OpenStack instance provision with default parameters'
                       '(required, e.g.: http://example.com/api/template-groups/16c7675752244f5d9e870a2cb0cfeb02/)',
        'username': 'NodeConductor user username (e.g. Username)',
        'password': 'NodeConductor user password (e.g. Password)',
    }
    SERVICE_ACCOUNT_EXTRA_FIELDS = {
        'license_code': 'License code that will be used for SugarCRM activation. (required)',
        'user_data': 'User data that will be passed to CRMs OpenStack instance on creation.'
                     'Word {password} will be replaced with auto-generated admin password. '
                     ' (default: "#cloud-config:\nruncmd:\n - [bootstrap, -p, {password}]")',
        'protocol': 'CRMs access protocol. (default: "http")',
    }

    class Meta(structure_serializers.BaseServiceSerializer.Meta):
        model = models.SugarCRMService
        view_name = 'sugarcrm-detail'

    def get_fields(self):
        fields = super(ServiceSerializer, self).get_fields()
        fields['protocol'].initial = backend.SugarCRMBackend.DEFAULT_PROTOCOL
        fields['user_data'].initial = backend.SugarCRMBackend.DEFAULT_USER_DATA
        return fields


class ServiceProjectLinkSerializer(structure_serializers.BaseServiceProjectLinkSerializer):
    quotas = quotas_serializers.QuotaSerializer(many=True, read_only=True)

    class Meta(structure_serializers.BaseServiceProjectLinkSerializer.Meta):
        model = models.SugarCRMServiceProjectLink
        view_name = 'sugarcrm-spl-detail'
        extra_kwargs = {
            'service': {'lookup_field': 'uuid', 'view_name': 'sugarcrm-detail'},
        }
        fields = structure_serializers.BaseServiceProjectLinkSerializer.Meta.fields + ('quotas',)


class CRMSerializer(structure_serializers.BaseResourceSerializer):
    DEFAULT_USER_COUNT = 10
    service = serializers.HyperlinkedRelatedField(
        source='service_project_link.service',
        view_name='sugarcrm-detail',
        read_only=True,
        lookup_field='uuid')

    service_project_link = serializers.HyperlinkedRelatedField(
        view_name='sugarcrm-spl-detail',
        queryset=models.SugarCRMServiceProjectLink.objects.all(),
        write_only=True)

    user_count = serializers.IntegerField(min_value=0, default=DEFAULT_USER_COUNT, write_only=True)
    quotas = quotas_serializers.QuotaSerializer(many=True, read_only=True)

    class Meta(structure_serializers.BaseResourceSerializer.Meta):
        model = models.CRM
        view_name = 'sugarcrm-crms-detail'
        fields = structure_serializers.BaseResourceSerializer.Meta.fields + ('api_url', 'user_count', 'quotas')
        read_only_fields = ('api_url', )

    def validate(self, attrs):
        spl = attrs['service_project_link']
        quota = spl.quotas.get(name='user_limit_count')
        delta = attrs.get('user_count', self.DEFAULT_USER_COUNT)
        if quota.is_exceeded(delta=delta):
            raise serializers.ValidationError(
                'Service project link users count quota is over limit (limit: %s, required: %s)' %
                (quota.limit, quota.usage + delta))
        return attrs


class CRMUserSerializer(serializers.Serializer):

    url = serializers.SerializerMethodField()
    uuid = serializers.CharField(read_only=True, source='id')
    user_name = serializers.CharField(max_length=60)
    password = serializers.CharField(write_only=True, max_length=255)
    status = serializers.CharField(read_only=True)
    last_name = serializers.CharField(max_length=30)
    first_name = serializers.CharField(max_length=30, required=False)
    email = serializers.CharField(source='email1', max_length=255, required=False)

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

    def validate(self, attrs):
        crm = self.context['crm']
        user_count_quota = crm.quotas.get(name='user_count')
        if user_count_quota.is_exceeded(delta=1):
            raise serializers.ValidationError(
                'User count quota is over limit (users count: %s, max users count: %s).' %
                (user_count_quota.usage, user_count_quota.limit))
        return attrs
