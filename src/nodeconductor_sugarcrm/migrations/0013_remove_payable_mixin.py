# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nodeconductor_sugarcrm', '0012_remove_spl_state'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='crm',
            name='billing_backend_id',
        ),
        migrations.RemoveField(
            model_name='crm',
            name='last_usage_update_time',
        ),
    ]
