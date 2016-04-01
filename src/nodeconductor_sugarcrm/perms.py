from nodeconductor.structure import perms as structure_perms


PERMISSION_LOGICS = (
    ('nodeconductor_sugarcrm.SugarCRMService', structure_perms.service_permission_logic),
    ('nodeconductor_sugarcrm.SugarCRMServiceProjectLink', structure_perms.service_project_link_permission_logic),
    ('nodeconductor_sugarcrm.CRM', structure_perms.resource_permission_logic),
)
