from django.apps import AppConfig


class ParlorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'parlor'
    
    def ready(self):
        import parlor.signals #this activates the signals
