from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # Auth & landing
    path('', include('accounts.urls')),

    # Assigner portal
    path('assigner/', include('portals.assigner_urls')),

    # Doctor portal
    path('doctor/', include(('portals.doctor_urls', 'doctor'), namespace='doctor')),
]

from django.conf import settings
from django.conf.urls.static import static
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
