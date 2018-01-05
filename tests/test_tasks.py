from __future__ import absolute_import, division, print_function, unicode_literals

from django.test import TestCase
from mock import mock

from quade import managers
from quade.models import Record
from quade.tasks import execute_test_task

from . import factories
from .mock import QuadeMock


class TestExecuteTask(TestCase):

    def test_execute_unit(self):
        record = factories.Record()
        with mock.patch('quade.models.Record.execute_test') as mock_execute:
            execute_test_task(record.id)
            mock_execute.assert_called_once()

    @QuadeMock(managers)
    def test_execute_functional(self):
        record = factories.Record(scenario__config=[('customer', {})])
        execute_test_task(record.id)
        record.refresh_from_db()
        self.assertEqual(record.status, Record.Status.READY)
