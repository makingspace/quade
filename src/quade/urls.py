from __future__ import absolute_import, division, print_function, unicode_literals

from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.MainView.as_view(), name='qa-main'),
    url(
        r'^record/(?P<test_record_id>[0-9]+)/done/$',
        views.MarkDoneView.as_view(),
        name='qa-mark-done'
    ),
]
