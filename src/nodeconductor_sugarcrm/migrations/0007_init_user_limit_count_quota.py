# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from uuid import uuid4

from django.contrib.contenttypes.models import ContentType
from django.db import migrations


USER_LIMIT_COUNT_QUOTA = 'user_limit_count'
USER_COUNT_QUOTA = 'user_count'


def init_spls_quotas(apps, schema_editor):
    Quota = apps.get_model('quotas', 'Quota')
    SugarCRMServiceProjectLink = apps.get_model('nodeconductor_sugarcrm', 'SugarCRMServiceProjectLink')
    CRM = apps.get_model('nodeconductor_sugarcrm', 'CRM')
    spl_ct = ContentType.objects.get_for_model(SugarCRMServiceProjectLink)
    crm_ct = ContentType.objects.get_for_model(CRM)

    for spl in SugarCRMServiceProjectLink.objects.all():
        spl_kwargs = {'content_type_id': spl_ct.id, 'object_id': spl.id}
        if not Quota.objects.filter(name=USER_LIMIT_COUNT_QUOTA, **spl_kwargs).exists():
            usage = 0
            for crm in spl.crms.all():
                usage += Quota.objects.get(name=USER_COUNT_QUOTA, content_type_id=crm_ct.id, object_id=crm.id).limit
            Quota.objects.create(
                uuid=uuid4().hex, name=USER_LIMIT_COUNT_QUOTA, usage=usage, **spl_kwargs)


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0001_initial'),
        ('nodeconductor_sugarcrm', '0006_resource_error_message'),
    ]

    operations = [
        migrations.RunPython(init_spls_quotas),
    ]
