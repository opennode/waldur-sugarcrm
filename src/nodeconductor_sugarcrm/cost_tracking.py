from django.contrib.contenttypes.models import ContentType

from nodeconductor.cost_tracking import CostTrackingBackend
from nodeconductor.cost_tracking.models import DefaultPriceListItem

from .models import CRM


USERS = 'users'
USERS_KEY = 'count'
SUPPORT = 'support'
SUPPORT_KEY = 'premium'


class SugarCRMCostTrackingBackend(CostTrackingBackend):
    NUMERICAL = [USERS]

    @classmethod
    def get_default_price_list_items(cls):
        content_type = ContentType.objects.get_for_model(CRM)

        yield DefaultPriceListItem(
            item_type=USERS, key=USERS_KEY,
            resource_content_type=content_type)

        yield DefaultPriceListItem(
            item_type=SUPPORT, key=SUPPORT_KEY,
            resource_content_type=content_type)

    @classmethod
    def get_used_items(cls, resource):
        user_count = resource.quotas.get(name=resource.Quotas.user_count).limit
        return [(USERS, USERS_KEY, user_count)]
