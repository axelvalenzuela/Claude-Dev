"""Project-level URL map: /admin/ is the whole approval interface (see
expenses/admin/), /accounts/ is auth, /reports/ is the employee portal.
Media files are only served by Django itself in DEBUG — a real deployment
would put a web server or storage service in front of them instead."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.urls import include, path
from django.views.generic import RedirectView

from .views import health_check

urlpatterns = [
    path('healthz', health_check, name='health-check'),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('reports/', include('expenses.urls')),
    path('', login_required(RedirectView.as_view(pattern_name='reports:list')), name='home'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
