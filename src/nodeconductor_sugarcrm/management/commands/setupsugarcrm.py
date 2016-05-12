# -*- coding: utf-8

from __future__ import unicode_literals

import urllib

from django.core.management.base import BaseCommand
from django.core.urlresolvers import reverse
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType

from ...models import CRM
from nodeconductor_openstack import models as openstack_models
from nodeconductor.structure import models as structure_models, SupportedServices
from nodeconductor.template import models as template_models


class Command(BaseCommand):
    help_text = "Setup templates, service settings and services for SugarCRM default workflow"

    def handle(self, *args, **options):
        self.created_instances = []
        try:
            self.setup()
        except:
            self.rollback()
            self.stdout.write(self.style.NOTICE('  Error happened, rolling back all changes'))
            raise

    def setup(self):
        self.stdout.write(self.style.MIGRATE_HEADING('Preparation:'))
        self.base_url = (raw_input('Please enter NodeConductor base URL [http://127.0.0.1:8000]:') or
                         'http://127.0.0.1:8000')

        self.stdout.write(
            'Steps for SugarCRM setup:\n'
            ' 1. Create SugarCRM MO Customer and Project.\n'
            ' 2. Create Owner for SugarCRM MO Customer.\n'
            ' 3. Create OpenStack service settings and OpenStack service.\n'
            ' 4. Create Zabbix service settings and Zabbix service (optional).\n'
            ' 5. Create Template Group for OpenStack instance + Zabbix host.\n'
            ' 6. Create Service settings for SugarCRM.\n'
            ' 7. Create SugarCRM template.\n'
        )

        self.stdout.write(self.style.MIGRATE_HEADING('Step 1: SugarCRM MO Customer and Project'))
        # customer
        customer_name = raw_input('  Enter customer name [SugarCRM MO customer]:') or 'SugarCRM MO customer'
        customer = structure_models.Customer.objects.create(name=customer_name)
        self.created_instances.append(customer)
        customer_detail_url = self._get_admin_detail_url(customer)
        self.stdout.write('  Customer was created with given name. You can edit its details here: {}'.format(
            customer_detail_url))
        # project
        project_name = raw_input('  Enter project name [SugarCRM MO project]:') or 'SugarCRM MO project'
        project = structure_models.Project.objects.create(name=project_name, customer=customer)
        self.created_instances.append(project)
        project_detail_url = self._get_admin_detail_url(project)
        self.stdout.write('  Project was created with given name. You can edit its details here: {}'.format(
            project_detail_url))

        self.stdout.write(self.style.MIGRATE_HEADING('Step 2: Owner for SugarCRM MO Customer'))
        # user
        while True:
            username = raw_input('  Enter username of SugarCRM customer owner [SugarCRM user]:') or 'SugarCRM user'
            if get_user_model().objects.filter(username=username).exists():
                self.stdout.write('  User with such username already exists. Please choose another one.')
            else:
                break
        password = raw_input('  Enter password of SugarCRM customer owner [password]:') or 'password'
        user = get_user_model().objects.create_user(username=username, password=password)
        self.created_instances.append(user)
        customer.add_user(user, structure_models.CustomerRole.OWNER)
        user_detail_url = self._get_admin_detail_url(user)
        self.stdout.write('  Customer owner was created successfully, you can edit his details here: {}'.format(
            user_detail_url))

        self.stdout.write(self.style.MIGRATE_HEADING('Step 3: Owner for SugarCRM MO Customer'))
        # OpenStack service settings
        openstack_settings_name = (raw_input('  Enter OpenStack service settings name [SugarCRM MO OpenStack settings]:')
                                   or 'SugarCRM MO OpenStack settings')
        openstack_settings_url = self._get_admin_add_url(structure_models.ServiceSettings)
        defaults = {'customer': customer.id, 'type': 'OpenStack', 'name': openstack_settings_name, 'shared': ''}
        openstack_settings_url += '?' + urllib.urlencode(defaults)
        self.stdout.write('  Go to URL: {} and create new OpenStack service settings'.format(openstack_settings_url))
        while True:
            openstack_settings_id = raw_input('  Enter created service settings id:')
            try:
                openstack_settings = structure_models.ServiceSettings.objects.get(id=openstack_settings_id)
            except (structure_models.ServiceSettings.DoesNotExist, ValueError):
                self.stdout.write('  There is no service settings with given id, please try again.')
            else:
                self.created_instances.append(openstack_settings)
                self.stdout.write('  ServiceSettings was created successfully.')
                break
        # OpenStack service
        openstack_service_name = (raw_input('  Enter OpenStack service name [SugarCRM MO service]:')
                                  or 'SugarCRM MO service')
        openstack_service = openstack_models.OpenStackService.objects.create(
            settings=openstack_settings, name=openstack_service_name, customer=customer, available_for_all=True)
        self.created_instances[-1] = openstack_service
        self.stdout.write('  OpenStack service was created successfully.')

        if not SupportedServices.has_service_type('Zabbix'):
            self.stdout.write('Step 4: Skipped. Zabbix is not installed')
            is_zabbix_enabled = False
        else:
            from nodeconductor_zabbix import models as zabbix_models
            is_zabbix_enabled = True
            self.stdout.write(self.style.MIGRATE_HEADING('Step 4: Create Zabbix service settings and Zabbix service'))
            # Zabbix service settings
            zabbix_settings_name = (raw_input('  Enter Zabbix service settings name [SugarCRM MO Zabbix settings]:')
                                    or 'SugarCRM MO Zabbix settings')
            zabbix_settings_url = self._get_admin_add_url(structure_models.ServiceSettings)
            defaults = {'customer': customer.id, 'type': 'Zabbix', 'name': zabbix_settings_name, 'shared': ''}
            zabbix_settings_url += '?' + urllib.urlencode(defaults)
            self.stdout.write('  Go to URL: {} and create new OpenStack service settings'.format(zabbix_settings_url))
            while True:
                zabbix_settings_id = raw_input('  Enter created service settings id:')
                try:
                    zabbix_settings = structure_models.ServiceSettings.objects.get(id=zabbix_settings_id)
                except (structure_models.ServiceSettings.DoesNotExist, ValueError):
                    self.stdout.write('  There is no service settings with given id, please try again.')
                else:
                    self.created_instances.append(zabbix_settings)
                    self.stdout.write('  ServiceSettings was created successfully.')
                    break
            # Zabbix service
            zabbix_service_name = raw_input('  Enter Zabbix service name [SugarCRM MO service]:') or 'SugarCRM MO service'
            zabbix_service = zabbix_models.ZabbixService.objects.create(
                settings=zabbix_settings, name=zabbix_service_name, customer=customer, available_for_all=True)
            self.created_instances[-1] = zabbix_service
            self.stdout.write('  Zabbix service was created successfully.')

        self.stdout.write(self.style.MIGRATE_HEADING('Step 5: Template Group for OpenStack instance + Zabbix host'))
        # internal template group
        while True:
            template_group_name = (raw_input('  Enter internal template group name [SugarCRM internal]:')
                                   or 'SugarCRM internal')
            if template_models.TemplateGroup.objects.filter(name=template_group_name).exists():
                self.stdout.write(self.style.NOTICE(
                    '  Template group with such name already exists. Enter another one.'))
            else:
                break
        template_group = template_models.TemplateGroup.objects.create(name=template_group_name)
        template_group.tags.add('internal')
        self.created_instances.append(template_group)
        # OpenStack instance template
        project_url = self.base_url + reverse('project-detail', args=(project.uuid.hex,))
        service_url = self.base_url + reverse('openstack-detail', args=(openstack_service.uuid.hex,))
        instance_template = template_group.templates.create(
            order_number=1,
            resource_content_type=ContentType.objects.get_for_model(openstack_models.Instance),
            options={'project': project_url, 'service': service_url})
        self.created_instances.append(instance_template)
        template_group_detail_url = self._get_admin_detail_url(template_group)
        self.stdout.write('  Base OpenStack template group was created successfully.')
        while True:
            required_fields = 'flavor', 'image', 'system_volume_size', 'security_groups', 'data_volume_size'
            self.stdout.write('  Please go to URL {} and define {} for OpenStack instance template'.format(
                ', '.join(required_fields), template_group_detail_url))
            raw_input('  Press enter to continue')
            instance_template = template_group.templates.get(id=instance_template.id)
            instance_template_valid = True
            for field in required_fields:
                if field not in instance_template.options:
                    self.stdout.write(self.style.NOTICE(
                        '  Field {} has to be defined in OpenStack instance template'.format(field)))
                    instance_template_valid = False
            if instance_template_valid:
                break
        self.stdout.write('  OpenStack instance template was created successfully.')
        # Zabbix template
        if is_zabbix_enabled:
            service_url = self.base_url + reverse('zabbix-detail', args=(zabbix_service.uuid.hex,))
            host_template = template_group.templates.create(
                order_number=2,
                resource_content_type=ContentType.objects.get_for_model(zabbix_models.Host),
                options={'name': '{{ response.backend_id }}',
                         'visible_name': '{{ response.name }}',
                         'scope': '{{ response.url }}',
                         'project': project_url, 'service': service_url})
            self.created_instances.append(host_template)
        self.stdout.write('  Zabbix host template was created successfully.')
        self.stdout.write('  Internal template group with templates was created successfully.')

        self.stdout.write(self.style.MIGRATE_HEADING('Step 6: Service settings for SugarCRM'))
        # SugarCRM service settings
        sugarcrm_settings_name = (raw_input('  Enter SugarCRM service settings name [SugarCRM settings]:') or
                                  'SugarCRM settings')
        license_code = raw_input('  Enter SugarCRM license code:')
        protocol = raw_input('  Enter SugarCRM CRMs protocol [http]:') or 'http'
        while True:
            shared = raw_input('  Make settings shared? [Y/n]:') or 'y'
            if shared.lower() not in ('y', 'n'):
                self.stdout.write('  Please enter letter "y" or "n"')
            else:
                shared = shared.lower() == 'y'
                break
        tg_url = self.base_url + reverse('template-group-detail', args=(template_group.uuid.hex,))
        sugarcrm_settings = structure_models.ServiceSettings.objects.create(
            name=sugarcrm_settings_name,
            backend_url=tg_url,
            username=username,
            password=password,
            type='SugarCRM',
            shared=shared,
            options={'license_code': license_code, 'protocol': protocol})
        self.created_instances.append(sugarcrm_settings)
        settings_admin_url = self._get_admin_detail_url(sugarcrm_settings)
        self.stdout.write('  SugarCRM service settings was created successfully, you can edit them details here: {}'
                          .format(settings_admin_url))

        self.stdout.write(self.style.MIGRATE_HEADING('Step 7: SugarCRM template group'))
        # external template group
        while True:
            template_group_name = raw_input('  Enter SugarCRM external template group name [SugarCRM]:') or 'SugarCRM'
            if template_models.TemplateGroup.objects.filter(name=template_group_name).exists():
                self.stdout.write(self.style.NOTICE(
                    '  Template group with such name already exists. Enter another one.'))
            else:
                break
        template_group = template_models.TemplateGroup.objects.create(name=template_group_name)
        template_group.tags.add('SaaS')
        self.created_instances.append(template_group)
        # templates for template group
        settings_url = self.base_url + reverse('servicesettings-detail', args=(sugarcrm_settings.uuid.hex,))
        template = template_group.templates.create(
            order_number=1,
            resource_content_type=ContentType.objects.get_for_model(CRM),
            options={'service_settings': settings_url}
        )
        template.tags.add('IaaS')
        self.created_instances.append(template)
        template_group_admin_url = self._get_admin_detail_url(template_group)
        self.stdout.write('  External template group with templates was created successfully, you can edit its details '
                          'here: {}'.format(template_group_admin_url))
        self.stdout.write(self.style.MIGRATE_HEADING('SugarCRM setup was finished successfully.'))
        template_group_url = self.base_url + reverse('template-group-detail', args=(template_group.uuid.hex,))
        self.stdout.write('To test SugarCRM setup try to execute POST request against {} '
                          '("name" and "project" parameters are required)'.format(template_group_url + 'provision/'))

    def rollback(self):
        for instance in self.created_instances[::-1]:
            instance.delete()

    def _get_admin_detail_url(self, instance):
        name = 'admin:{app_label}_{model_name}_change'.format(
            app_label=instance._meta.app_label, model_name=instance._meta.model_name)
        return self.base_url + reverse(name, args=(instance.id,))

    def _get_admin_add_url(self, model):
        name = 'admin:{app_label}_{model_name}_add'.format(
            app_label=model._meta.app_label, model_name=model._meta.model_name)
        return self.base_url + reverse(name)
