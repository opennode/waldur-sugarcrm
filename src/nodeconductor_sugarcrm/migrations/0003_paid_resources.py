# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('nodeconductor_sugarcrm', '0002_add_crm_access_fields'),
        ('contenttypes', '0001_initial'),
        ('cost_tracking', '__latest__'),
    ]

    operations = [
        migrations.AddField(
            model_name='crm',
            name='billing_backend_id',
            field=models.CharField(help_text=b'ID of a resource in backend', max_length=255, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='crm',
            name='last_usage_update_time',
            field=models.DateTimeField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
