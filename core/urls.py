from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', include('public_pages.urls')),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('billing/', include('billing.urls')),
    path('clients/', include('clients.urls')),
    path('insurers/', include('insurers.urls')),
    path('coverages/', include('coverages.urls')),
    path('policies/', include('policies.urls')),
    path('claims/', include('claims.urls')),
    path('endorsements/', include('endorsements.urls')),
    path('renewals/', include('renewals.urls')),
    path('crm/', include('crm.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('reports/', include('reports.urls')),
    path('ai/', include('ai_agent.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
