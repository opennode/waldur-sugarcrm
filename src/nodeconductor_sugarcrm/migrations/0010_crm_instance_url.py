# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('nodeconductor_sugarcrm', '0009_remove_crm_size_field'),
    ]

    operations = [
        migrations.AddField(
            model_name='crm',
            name='instance_url',
            field=models.URLField(help_text='CRMs OpenStack instance URL in NC.', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='crm',
            name='api_url',
            field=models.CharField(help_text='CRMs OpenStack instance access URL.', max_length=127),
            preserve_default=True,
        ),
    ]
