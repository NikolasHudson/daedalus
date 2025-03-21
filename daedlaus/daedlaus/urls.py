"""
URL configuration for daedlaus project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.views.generic import TemplateView

def healthcheck(request):
    return JsonResponse({"status": "ok"})

def home(request):
    return TemplateView.as_view(template_name="index.html")(request)

def test_view(request):
    return TemplateView.as_view(template_name="test.html")(request)

# Configure admin site
admin.site.site_header = "Daedalus Administration"
admin.site.site_title = "Daedalus Admin Portal"
admin.site.index_title = "Welcome to Daedalus Legal Tech Platform"

urlpatterns = [
    path("", home, name="home"),
    path("test/", test_view, name="test"),
    path("admin/", admin.site.urls),
    path('api-auth/', include('rest_framework.urls')),
    
    # Include all authentication URLs under root path
    path('', include('users.urls')),
    
    # Include AWS admin validation URLs
    path('aws/', include('aws.urls', namespace='aws')),
    
    # Document management URLs 
    path('documents/', include('documents.urls')),
    
    # Case management URLs
    path('cases/', include('cases.urls')),
    
    # Client management URLs
    path('clients/', include('clients.urls')),
    
    # Docket management URLs
    path('docket/', include('docket.urls')),
    
    path('healthcheck/', healthcheck, name='healthcheck'),
]

# Add debug toolbar in development
if settings.DEBUG:
    try:
        import debug_toolbar
        urlpatterns.append(path('__debug__/', include(debug_toolbar.urls)))
    except ImportError:
        pass

# Serve static and media files
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
