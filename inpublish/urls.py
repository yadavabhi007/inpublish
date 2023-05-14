"""inpublish URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
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
from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.views.i18n import JavaScriptCatalog
from js_urls.views import JsUrlsView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("js-urls/", JsUrlsView.as_view(), name="js_urls"),
    path("i18n/", include("django.conf.urls.i18n")),
    path(
        "workers/",
        include("interattivo_worker.urls", namespace="interattivo_worker"),
    ),
]

urlpatterns += i18n_patterns(
    path("", include("builder.urls", namespace="builder")),
    path("jsi18n/", JavaScriptCatalog.as_view(), name="javascript-catalog"),
)


if settings.DEBUG:
    urlpatterns += static("/media/", document_root=settings.MEDIA_ROOT)
    # urlpatterns += static(settings.STATIC_URL,
    #                       document_root=settings.STATIC_ROOT)
