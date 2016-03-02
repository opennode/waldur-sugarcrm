from django.dispatch import Signal

# SugarCRM user signals
user_post_save = Signal(providing_args=['old_user', 'new_user', 'crm', 'created'])
user_post_delete = Signal(providing_args=['user', 'crm'])
