from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class DocumentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'documents'
    verbose_name = _('Document Management')
    
    def ready(self):
        """
        Initialize the documents app.
        Import signals and connect handlers.
        """
        # Import signals
        import documents.signals