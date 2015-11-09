# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('nodeconductor_sugarcrm', '0003_paid_resources'),
    ]

    operations = [
        migrations.AddField(
            model_name='sugarcrmserviceprojectlink',
            name='error_message',
            field=models.TextField(blank=True),
            preserve_default=True,
        ),
    ]
