from __future__ import absolute_import, division, print_function, unicode_literals

from mksp.apps.qa.models import QATestRecord
from mksp.celery import app


@app.task
def execute_test_task(record_id):
    record = QATestRecord.objects.get(id=record_id)
    record.execute_test()
