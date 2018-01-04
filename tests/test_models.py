from __future__ import absolute_import, division, print_function, unicode_literals

from django.contrib.auth import get_user_model
User = get_user_model()
from django.core.exceptions import ValidationError
from django.test import TestCase
from django_fsm.db.fields import TransitionNotAllowed
from mock import mock

from quade import managers
from quade.models import RecordedObject, Record, Scenario
from .mock import QuadeMock
from . import factories


class TestScenario(TestCase):

    def test_activate(self):
        scenario = factories.Scenario(config='')
        scenario.activate()
        self.assertEqual(scenario.status, Scenario.Status.ACTIVE)

    def test_deactivate(self):
        scenario = factories.Scenario(config='', status=Scenario.Status.INACTIVE)
        scenario.deactivate()
        self.assertEqual(scenario.status, Scenario.Status.INACTIVE)

    def test_delete(self):
        """Deleting a Scenario simply makes it inactive."""
        scenario = factories.Scenario(config='', status=Scenario.Status.INACTIVE)
        scenario.delete()
        self.assertEqual(scenario.status, Scenario.Status.INACTIVE)

    def test_hard_delete(self):
        scenario = factories.Scenario(config='')
        scenario.hard_delete()
        with self.assertRaises(Scenario.DoesNotExist):
            scenario.refresh_from_db()

    def test_active_queryset(self):
        active_scenarios = factories.Scenario.create_batch(3, config='')
        factories.Scenario(config='', status=Scenario.Status.INACTIVE)  # Noise
        self.assertQuerysetEqual(
            Scenario.objects.active(),
            [s.pk for s in active_scenarios],
            transform=lambda obj: obj.pk,
            ordered=False
        )

    def test_str(self):
        scenario = factories.Scenario(config='', description='A Nice Test')
        self.assertEqual(str(scenario), '#1: A Nice Test')


class TestModels(TestCase):

    @mock.patch('quade.models.manager')
    @QuadeMock(managers)
    def test_config_is_validated_on_creation(self, mocked_validate):
        factories.Scenario(config='')
        mocked_validate.validate.assert_called_once_with('')

    @QuadeMock(managers)
    def test_config_is_validated_on_update(self):
        scenario = factories.Scenario(config='')
        new_config = [('new', {})]
        scenario.config = new_config
        with mock.patch('quade.models.manager') as mocked_validate:
            scenario.save()
        mocked_validate.validate.assert_called_once_with(new_config)

    @QuadeMock(managers)
    def test_validation_error(self):
        bad_function = 'does_not_exist'
        good_function = 'staff_user'
        config = [(bad_function, {}), (good_function, {})]
        with self.assertRaises(ValidationError) as exc:
            factories.Scenario(config=config)
        self.assertEqual(
            exc.exception.message,
            "config {} contains unregistered function(s): {}".format(config, bad_function)
        )

    def test_execute_test_transition(self):
        record = factories.Record()
        record.execute_test()
        record.refresh_from_db()
        self.assertEqual(record.status, Record.Status.READY)

    def test_execute_test_only_once(self):
        record = factories.Record()
        record.execute_test()
        with self.assertRaises(TransitionNotAllowed):
            record.execute_test()

    @QuadeMock(managers)
    def test_execute_test_records_instructions(self):
        record = factories.Record(scenario__config=[('customer', {})])
        record.execute_test()
        record.refresh_from_db()
        self.assertIsNotNone(record.instructions)

    @QuadeMock(managers)
    def test_execute_test_tracks_objects(self):
        record = factories.Record(scenario__config=[('staff_user', {})])
        initial_recorded_object_count = RecordedObject.objects.count()
        self.assertFalse(record.recorded_objects.count())

        record.execute_test()

        self.assertGreater(RecordedObject.objects.count(), initial_recorded_object_count)
        self.assertTrue(record.recorded_objects.count())
        user_object = record.recorded_objects.first()
        self.assertTrue(isinstance(user_object.object, User))
        self.assertTrue(user_object.object.is_staff)

    @QuadeMock(managers)
    def test_signal_connection_and_disconnection(self):
        record = factories.Record(scenario__config=[('staff_user', {})])

        with mock.patch('quade.receivers.post_save') as mocked_post_save:
            record.execute_test()

        mocked_post_save.connect.assert_called_once()
        callback = mocked_post_save.connect.call_args[0][0]
        mocked_post_save.disconnect.assert_called_once_with(callback)

    @QuadeMock(managers)
    def test_recorded_objects_not_created_outside_test_execution(self):
        record = factories.Record(scenario__config=[('staff_user', {})])

        record.execute_test()

        recorded_object_count = RecordedObject.objects.count()
        factories.User()
        self.assertEqual(RecordedObject.objects.count(), recorded_object_count)

    @QuadeMock(managers)
    def test_execute_test_that_errors(self):
        record = factories.Record(scenario__config=[('customer', {})])
        with mock.patch('quade.models.manager') as mocked_manager:
            mocked_manager.create.side_effect = ValueError("Some error")
            with self.assertRaises(ValueError):
                record.execute_test()
        record.refresh_from_db()
        self.assertEqual(record.status, Record.Status.FAILED)
        self.assertRegexpMatches(record.instructions, r"^ValueError\((u)?'Some error',\)$")


class TestRecordedObject(TestCase):

    def test_str(self):
        recorded_object = factories.RecordedObject()
        self.assertEqual(
            str(recorded_object),
            "RecordedObject #1: {}".format(recorded_object.object)
        )
