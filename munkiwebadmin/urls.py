from django.urls import include, re_path
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic.base import RedirectView
from django.core.exceptions import ImproperlyConfigured

# Temporarily comment out admin to avoid corrupted Django package
# from django.contrib import admin

urlpatterns = [
    # re_path(r'^admin/', admin.site.urls),

    re_path(r'^login/$', auth_views.LoginView.as_view(), name='login'),
    re_path(r'^logout/$', auth_views.LogoutView.as_view(next_page='/login/'), name='logout'),
    re_path(r'^api/', include('api.urls')),
    re_path(r'^manifests/', include('manifests.urls')),
    re_path(r'^catalogs/', include('catalogs.urls')),
    re_path(r'^pkgsinfo/', include('pkgsinfo.urls')),
    re_path(r'^makecatalogs/', include('process.urls')),
    re_path(r'^$', RedirectView.as_view(url='/manifests/', permanent=False), name='manifests'),
]
# comment out the following if you are serving
# static files a different way
urlpatterns += staticfiles_urlpatterns()

# debug/development serving MEDIA files (icons)
try:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
except ImproperlyConfigured:
    print("**** MEDIA_URL or MEDIA_ROOT missing from settings.py       ****")
    print("**** copy MEDIA_URL or MEDIA_ROOT from settings_template.py ****")
    raise