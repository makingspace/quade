from __future__ import absolute_import, division, print_function, unicode_literals

from django.contrib.auth import get_user_model
User = get_user_model()
from django.test import TestCase

from quade import managers
from tests.mock import QaMock
from tests import factories


class TestFixtureManager(TestCase):

    @QaMock(managers)
    def test_create_fixtures(self):
        initial_user_count = User.objects.count()
        scenario = factories.QATestScenario(
            config=[('customer', {}), ('staff_user', {})]
        )
        managers.manager.create(scenario.config)
        self.assertEqual(User.objects.count(), initial_user_count + 2)
        self.assertEqual(User.objects.filter(is_staff=False).count(), 1)
        self.assertEqual(User.objects.filter(is_staff=False).count(), 1)

    @QaMock(managers)
    def test_create_fixtures_with_kwargs(self):
        initial_user_count = User.objects.count()
        first_name = 'Baron'
        last_name = 'von Count'
        scenario = factories.QATestScenario(config=[('staff_user', {'first_name': first_name, 'last_name': last_name})])
        managers.manager.create(scenario.config)
        self.assertEqual(User.objects.count(), initial_user_count + 1)
        # Get the newly created User.
        new_staff = User.objects.last()
        self.assertEqual(new_staff.first_name, first_name)
        self.assertEqual(new_staff.last_name, last_name)

    @QaMock(managers)
    def test_validation_succeeds(self):
        good_function = 'staff_user'
        config = [(good_function, {})]
        managers.manager.validate(config)

    @QaMock(managers)
    def test_validation_fails(self):
        bad_function = 'does_not_exist'
        good_function = 'staff_user'
        config = [(bad_function, {}), (good_function, {})]
        with self.assertRaises(managers.ConfigurationError) as exc:
            managers.manager.validate(config)
        self.assertEqual(exc.exception.unregistered_functions, set([bad_function]))
