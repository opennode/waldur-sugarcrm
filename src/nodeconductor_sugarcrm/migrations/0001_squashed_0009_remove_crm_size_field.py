# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import taggit.managers
import django_fsm
import nodeconductor.core.models
import django.db.models.deletion
import django.utils.timezone
import nodeconductor.logging.loggers
import uuidfield.fields
import django.core.validators
import model_utils.fields
import nodeconductor.core.validators


class Migration(migrations.Migration):

    replaces = [(b'nodeconductor_sugarcrm', '0001_initial'), (b'nodeconductor_sugarcrm', '0002_add_crm_access_fields'), (b'nodeconductor_sugarcrm', '0003_paid_resources'), (b'nodeconductor_sugarcrm', '0004_add_error_message'), (b'nodeconductor_sugarcrm', '0005_crm_size'), (b'nodeconductor_sugarcrm', '0006_resource_error_message'), (b'nodeconductor_sugarcrm', '0007_init_user_limit_count_quota'), (b'nodeconductor_sugarcrm', '0008_crm_tags'), (b'nodeconductor_sugarcrm', '0009_remove_crm_size_field')]

    dependencies = [
        ('taggit', '0002_auto_20150616_2121'),
        ('structure', '0024_add_sugarcrm_to_settings'),
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SugarCRMService',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=150, verbose_name='name', validators=[nodeconductor.core.validators.validate_name])),
                ('uuid', uuidfield.fields.UUIDField(unique=True, max_length=32, editable=False, blank=True)),
                ('settings', models.ForeignKey(to='structure.ServiceSettings')),
                ('customer', models.ForeignKey(to='structure.Customer')),
                ('available_for_all', models.BooleanField(default=False, help_text='Service will be automatically added to all customers projects if it is available for all')),
            ],
            options={
                'abstract': False,
                'verbose_name': 'SugarCRM service',
                'verbose_name_plural': 'SugarCRM services',
            },
            bases=(nodeconductor.core.models.SerializableAbstractMixin, nodeconductor.logging.loggers.LoggableMixin, models.Model),
        ),
        migrations.CreateModel(
            name='SugarCRMServiceProjectLink',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('state', django_fsm.FSMIntegerField(default=5, choices=[(0, 'New'), (5, 'Creation Scheduled'), (6, 'Creating'), (1, 'Sync Scheduled'), (2, 'Syncing'), (3, 'In Sync'), (4, 'Erred')])),
                ('project', models.ForeignKey(to='structure.Project')),
                ('service', models.ForeignKey(to='nodeconductor_sugarcrm.SugarCRMService')),
                ('error_message', models.TextField(blank=True)),
            ],
            bases=(nodeconductor.core.models.SerializableAbstractMixin, nodeconductor.logging.loggers.LoggableMixin, models.Model),
            options={
                'verbose_name': 'SugarCRM service project link',
                'verbose_name_plural': 'SugarCRM service project links',
            },
        ),
        migrations.AlterUniqueTogether(
            name='sugarcrmserviceprojectlink',
            unique_together=set([('service', 'project')]),
        ),
        migrations.AlterUniqueTogether(
            name='sugarcrmservice',
            unique_together=set([('customer', 'settings')]),
        ),
        migrations.AddField(
            model_name='sugarcrmservice',
            name='projects',
            field=models.ManyToManyField(related_name='sugarcrm_services', through='nodeconductor_sugarcrm.SugarCRMServiceProjectLink', to=b'structure.Project'),
        ),
        migrations.CreateModel(
            name='CRM',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('description', models.CharField(max_length=500, verbose_name='description', blank=True)),
                ('name', models.CharField(max_length=150, verbose_name='name', validators=[nodeconductor.core.validators.validate_name])),
                ('uuid', uuidfield.fields.UUIDField(unique=True, max_length=32, editable=False, blank=True)),
                ('backend_id', models.CharField(max_length=255, blank=True)),
                ('start_time', models.DateTimeField(null=True, blank=True)),
                ('state', django_fsm.FSMIntegerField(default=1, help_text='WARNING! Should not be changed manually unless you really know what you are doing.', choices=[(1, 'Provisioning Scheduled'), (2, 'Provisioning'), (3, 'Online'), (4, 'Offline'), (5, 'Starting Scheduled'), (6, 'Starting'), (7, 'Stopping Scheduled'), (8, 'Stopping'), (9, 'Erred'), (10, 'Deletion Scheduled'), (11, 'Deleting'), (13, 'Resizing Scheduled'), (14, 'Resizing'), (15, 'Restarting Scheduled'), (16, 'Restarting')])),
                ('service_project_link', models.ForeignKey(related_name='crms', on_delete=django.db.models.deletion.PROTECT, to='nodeconductor_sugarcrm.SugarCRMServiceProjectLink')),
                ('error_message', models.TextField(blank=True)),
                ('tags', taggit.managers.TaggableManager(to='taggit.Tag', through='taggit.TaggedItem', blank=True, help_text='A comma-separated list of tags.', verbose_name='Tags')),
                ('admin_username', models.CharField(max_length=60)),
                ('admin_password', models.CharField(max_length=255)),
                ('api_url', models.CharField(help_text=b'CRMs OpenStack instance URL', max_length=127)),
                ('billing_backend_id', models.CharField(help_text=b'ID of a resource in backend', max_length=255, blank=True)),
                ('last_usage_update_time', models.DateTimeField(null=True, blank=True)),
            ],
            options={
                'abstract': False,
                'verbose_name': 'CRM',
                'verbose_name_plural': 'CRMs',
            },
            bases=(nodeconductor.core.models.SerializableAbstractMixin, nodeconductor.logging.loggers.LoggableMixin, models.Model),
        ),
    ]
