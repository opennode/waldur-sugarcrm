from django.contrib.contenttypes.models import ContentType

from . import models
from nodeconductor.cost_tracking import CostTrackingBackend
from nodeconductor.cost_tracking.models import DefaultPriceListItem
from nodeconductor.structure import ServiceBackend


class PriceItemTypes(object):
    USERS = 'users'
    STORAGE = 'storage'


class SugarCRMCostTrackingBackend(CostTrackingBackend):
    STORAGE_KEY = '1 GB'
    USERS_KEY = 'count'

    @classmethod
    def get_default_price_list_items(cls):
        crm_content_type = ContentType.objects.get_for_model(models.CRM)
        items = []
        # users
        items.append(DefaultPriceListItem(
            item_type=PriceItemTypes.USERS, key=cls.USERS_KEY, resource_content_type=crm_content_type))
        # storage
        items.append(DefaultPriceListItem(
            item_type=PriceItemTypes.STORAGE, key=cls.STORAGE_KEY, resource_content_type=crm_content_type))
        return items

    @classmethod
    def get_used_items(cls, resource):
        items = []
        # users
        user_count_limit = resource.quotas.get(name='user_count').limit
        items.append((PriceItemTypes.USERS, cls.USERS_KEY, user_count_limit))
        # storage
        items.append((PriceItemTypes.STORAGE, cls.STORAGE_KEY, ServiceBackend.mb2gb(resource.size)))
        return items
