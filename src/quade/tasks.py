from __future__ import absolute_import, division, print_function, unicode_literals

from celery import shared_task

from .models import Record


@shared_task
def execute_test_task(record_id):
    record = Record.objects.get(id=record_id)
    record.execute_test()
