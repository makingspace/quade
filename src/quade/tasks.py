from __future__ import absolute_import, division, print_function, unicode_literals

from .models import QATestRecord
from celery.task import task


@task
def execute_test_task(record_id):
    record = QATestRecord.objects.get(id=record_id)
    record.execute_test()
