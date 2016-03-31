# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nodeconductor_sugarcrm', '0011_crm_publishing_state'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='sugarcrmserviceprojectlink',
            name='error_message',
        ),
        migrations.RemoveField(
            model_name='sugarcrmserviceprojectlink',
            name='state',
        ),
    ]
