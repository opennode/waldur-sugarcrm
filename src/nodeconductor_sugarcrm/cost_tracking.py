from django.contrib.contenttypes.models import ContentType

from . import models
from nodeconductor.cost_tracking import CostTrackingBackend
from nodeconductor.cost_tracking.models import DefaultPriceListItem
from nodeconductor.structure import ServiceBackend


class PriceItemTypes(object):
    USAGE = 'usage'
    STORAGE = 'storage'


class SugarCRMCostTrackingBackend(CostTrackingBackend):
    STORAGE_KEY = '1 GB'
    USAGE_KEY = 'basic'

    @classmethod
    def get_default_price_list_items(cls):
        crm_content_type = ContentType.objects.get_for_model(models.CRM)
        items = []
        # usage
        items.append(DefaultPriceListItem(
            item_type=PriceItemTypes.USAGE, key=cls.USAGE_KEY, resource_content_type=crm_content_type))
        # storage
        items.append(DefaultPriceListItem(
            item_type=PriceItemTypes.STORAGE, key=cls.STORAGE_KEY, resource_content_type=crm_content_type))
        return items

    @classmethod
    def get_used_items(cls, resource):
        items = []
        # usage
        items.append((PriceItemTypes.USAGE, cls.USAGE_KEY, 1))
        # storage
        items.append((PriceItemTypes.STORAGE, cls.STORAGE_KEY, ServiceBackend.mb2gb(resource.size)))
        return items
