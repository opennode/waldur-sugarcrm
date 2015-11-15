# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('nodeconductor_sugarcrm', '0004_add_error_message'),
    ]

    operations = [
        migrations.AddField(
            model_name='crm',
            name='size',
            field=models.PositiveIntegerField(default=2048, help_text=b'Size of CRMs OpenStack instance data volume in MiB', validators=[django.core.validators.MinValueValidator(1024), django.core.validators.MaxValueValidator(10240)]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='crm',
            name='api_url',
            field=models.CharField(help_text=b'CRMs OpenStack instance URL', max_length=127),
            preserve_default=True,
        ),
    ]
