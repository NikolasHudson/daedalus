from django.apps import AppConfig


class ClientsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "clients"
    verbose_name = "Client Management"
    
    def ready(self):
        # Import signals to register them
        try:
            import clients.signals
        except ImportError:
            pass