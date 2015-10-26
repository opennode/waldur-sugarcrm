# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('nodeconductor_sugarcrm', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='crm',
            name='admin_password',
            field=models.CharField(default='admin', max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='crm',
            name='admin_username',
            field=models.CharField(default='admin', max_length=60),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='crm',
            name='api_url',
            field=models.CharField(default='http://127.0.0.1:2080', max_length=127),
            preserve_default=False,
        ),
    ]
