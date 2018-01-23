from __future__ import absolute_import, division, print_function, unicode_literals

import os

from django.test import TestCase
from mock import mock

from quade import managers
from quade.models import Record

from . import factories
from .mock import QuadeMock
from .utils import requires_celery


class TestExecuteTask(TestCase):

    @requires_celery
    def test_execute_unit(self):
        from quade.tasks import execute_test_task
        record = factories.Record()
        with mock.patch('quade.models.Record.execute_test') as mock_execute:
            execute_test_task(record.id)
            mock_execute.assert_called_once()

    @QuadeMock(managers)
    @requires_celery
    def test_execute_functional(self):
        from quade.tasks import execute_test_task
        record = factories.Record(scenario__config=[('customer', {})])
        execute_test_task(record.id)
        record.refresh_from_db()
        self.assertEqual(record.status, Record.Status.READY)
