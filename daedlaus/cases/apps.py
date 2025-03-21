from django.apps import AppConfig


class CasesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "cases"
    verbose_name = 'Case Management'
    
    def ready(self):
        # Import signals to register them
        try:
            import cases.signals
        except ImportError:
            pass