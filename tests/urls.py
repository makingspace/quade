from django.conf.urls import include, url

urlpatterns = [
    url(r'^quade/', include('quade.urls')),
]
