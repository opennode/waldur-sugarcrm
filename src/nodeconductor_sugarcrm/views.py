from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets, exceptions
from rest_framework.response import Response

from nodeconductor.structure import views as structure_views
from nodeconductor.structure.managers import filter_queryset_for_user
from . import models, serializers


class SugarCRMServiceViewSet(structure_views.BaseServiceViewSet):
    queryset = models.SugarCRMService.objects.all()
    serializer_class = serializers.ServiceSerializer


class SugarCRMServiceProjectLinkViewSet(structure_views.BaseServiceProjectLinkViewSet):
    queryset = models.SugarCRMServiceProjectLink.objects.all()
    serializer_class = serializers.ServiceProjectLinkSerializer


class CRMViewSet(structure_views.BaseOnlineResourceViewSet):
    queryset = models.CRM.objects.all()
    serializer_class = serializers.CRMSerializer

    def perform_provision(self, serializer):
        resource = serializer.save()
        backend = resource.get_backend()
        backend.provision(resource, user_count=serializer.validated_data['user_count'])


class CRMNotOnline(exceptions.APIException):
    status_code = 409


class CRMUserViewSet(viewsets.ViewSet):

    def initial(self, request, crm_uuid, *args, **kwargs):
        super(CRMUserViewSet, self).initial(request, crm_uuid, *args, **kwargs)
        queryset = filter_queryset_for_user(models.CRM.objects.all(), request.user)
        self.crm = get_object_or_404(queryset, uuid=crm_uuid)
        if self.crm.state != models.CRM.States.ONLINE:
            raise CRMNotOnline('Cannot execute user-related operations with CRM if it is not ONLINE')
        self.backend = self.crm.get_backend()

    def get_serializer_context(self):
        return {'crm': self.crm, 'request': self.request}

    # XXX: This method should be replaced by default filter then CRM users will be moved to separate model
    def get_filtered_users(self, request):
        supported_filters = ['first_name', 'last_name', 'user_name', 'status']
        filter_kwargs = {f: request.query_params[f] for f in supported_filters if f in request.query_params}
        return self.backend.list_users(**filter_kwargs)

    def list(self, request, crm_uuid):
        users = self.get_filtered_users(request)
        serializer = serializers.CRMUserSerializer(users, many=True, context=self.get_serializer_context())
        return Response(serializer.data)

    def retrieve(self, request, crm_uuid, pk=None):
        user = self.backend.get_user(pk)
        if user is None or int(user.is_admin):
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = serializers.CRMUserSerializer(user, context=self.get_serializer_context())
        return Response(serializer.data)

    def destroy(self, request, crm_uuid, pk=None):
        user = self.backend.get_user(pk)
        if user is None or int(user.is_admin):
            return Response(status=status.HTTP_404_NOT_FOUND)
        self.backend.delete_user(user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def create(self, request, crm_uuid):
        serializer = serializers.CRMUserSerializer(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        user = self.backend.create_user(status='Active', **serializer.validated_data)
        user_data = serializers.CRMUserSerializer(user, context=self.get_serializer_context()).data
        return Response(user_data, status=status.HTTP_201_CREATED)

    def update(self, request, crm_uuid, pk=None):
        return self.partial_update(self, request, crm_uuid, pk=None)

    def partial_update(self, request, crm_uuid, pk=None):
        user = self.backend.get_user(pk)
        if user is None or int(user.is_admin):
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = serializers.CRMUserSerializer(
            data=request.data, instance=user, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        user = self.backend.update_user(user, **serializer.validated_data)
        user_data = serializers.CRMUserSerializer(user, context=self.get_serializer_context()).data
        return Response(user_data, status.HTTP_200_OK)
