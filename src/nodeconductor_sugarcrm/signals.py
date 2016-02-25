from django.dispatch import Signal

# SugarCRM user signals
user_post_save = Signal(providing_args=['user', 'crm', 'created'])
user_post_delete = Signal(providing_args=['user', 'crm'])
