# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('nodeconductor_sugarcrm', '0008_crm_tags'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='crm',
            options={'verbose_name': 'CRM', 'verbose_name_plural': 'CRMs'},
        ),
        migrations.AlterModelOptions(
            name='sugarcrmservice',
            options={'verbose_name': 'SugarCRM service', 'verbose_name_plural': 'SugarCRM services'},
        ),
        migrations.AlterModelOptions(
            name='sugarcrmserviceprojectlink',
            options={'verbose_name': 'SugarCRM service project link', 'verbose_name_plural': 'SugarCRM service project links'},
        ),
        migrations.RemoveField(
            model_name='crm',
            name='size',
        ),
    ]
