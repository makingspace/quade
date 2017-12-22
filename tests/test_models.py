from __future__ import absolute_import, division, print_function, unicode_literals

from django.contrib.auth import get_user_model
User = get_user_model()
from django.core.exceptions import ValidationError
from django.test import TestCase, TransactionTestCase
from django_fsm.db.fields import TransitionNotAllowed
from mock import mock

from quade import managers
from quade.models import QAObject, QATestRecord
from .mock import QaMock
from . import factories


class TestQaModels(TransactionTestCase):

    @mock.patch('quade.models.manager')
    @QaMock(managers)
    def test_config_is_validated_on_creation(self, mocked_validate):
        factories.QATestScenario(config='')
        mocked_validate.validate.assert_called_once_with('')

    @QaMock(managers)
    def test_config_is_validated_on_update(self):
        scenario = factories.QATestScenario(config='')
        new_config = [('new', {})]
        scenario.config = new_config
        with mock.patch('quade.models.manager') as mocked_validate:
            scenario.save()
        mocked_validate.validate.assert_called_once_with(new_config)

    @QaMock(managers)
    def test_validation_error(self):
        bad_function = 'does_not_exist'
        good_function = 'staff_user'
        config = [(bad_function, {}), (good_function, {})]
        with self.assertRaises(ValidationError) as exc:
            factories.QATestScenario(config=config)
        self.assertEqual(
            exc.exception.message,
            "config {} contains unregistered function(s): {}".format(config, bad_function)
        )

    def test_execute_test_transition(self):
        record = factories.QATestRecord()
        record.execute_test()
        record.refresh_from_db()
        self.assertEqual(record.status, QATestRecord.Status.READY)

    def test_execute_test_only_once(self):
        record = factories.QATestRecord()
        record.execute_test()
        with self.assertRaises(TransitionNotAllowed):
            record.execute_test()

    @QaMock(managers)
    def test_execute_test_records_instructions(self):
        record = factories.QATestRecord(scenario__config=[('customer', {})])
        record.execute_test()
        record.refresh_from_db()
        self.assertIsNotNone(record.instructions)

    @QaMock(managers)
    def test_execute_test_tracks_objects(self):
        record = factories.QATestRecord(scenario__config=[('staff_user', {})])
        initial_qa_object_count = QAObject.objects.count()
        self.assertFalse(record.qa_objects.count())

        record.execute_test()

        self.assertGreater(QAObject.objects.count(), initial_qa_object_count)
        self.assertTrue(record.qa_objects.count())
        user_object = record.qa_objects.first()
        self.assertTrue(isinstance(user_object.object, User))
        self.assertTrue(user_object.object.is_staff)

    @QaMock(managers)
    def test_signal_connection_and_disconnection(self):
        record = factories.QATestRecord(scenario__config=[('staff_user', {})])

        with mock.patch('quade.receivers.post_save') as mocked_post_save:
            record.execute_test()

        mocked_post_save.connect.assert_called_once()
        callback = mocked_post_save.connect.call_args[0][0]
        mocked_post_save.disconnect.assert_called_once_with(callback)

    @QaMock(managers)
    def test_qa_objects_not_created_outside_test_execution(self):
        record = factories.QATestRecord(scenario__config=[('staff_user', {})])

        record.execute_test()

        qa_object_count = QAObject.objects.count()
        factories.User()
        self.assertEqual(QAObject.objects.count(), qa_object_count)

    @QaMock(managers)
    def test_execute_test_that_errors(self):
        record = factories.QATestRecord(scenario__config=[('customer', {})])
        with mock.patch('quade.models.manager') as mocked_manager:
            mocked_manager.create.side_effect = ValueError("Some error")
            with self.assertRaises(ValueError):
                record.execute_test()
        record.refresh_from_db()
        self.assertEqual(record.status, QATestRecord.Status.FAILED)
        self.assertEqual(record.instructions, "ValueError(u'Some error',)")
