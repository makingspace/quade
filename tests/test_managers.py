from __future__ import absolute_import, division, print_function, unicode_literals

from django.contrib.auth import get_user_model
User = get_user_model()
from django.test import TestCase

from quade import managers
from .mock import QuadeMock
from .fixtures import customer, staff_user_id


class TestExecution(TestCase):

    @QuadeMock(managers)
    def test_execute_fixtures(self):
        initial_user_count = User.objects.count()
        config = [('customer', {}), ('staff_user', {})]
        managers.manager.execute(config)
        self.assertEqual(User.objects.count(), initial_user_count + 2)
        self.assertEqual(User.objects.filter(is_staff=False).count(), 1)
        self.assertEqual(User.objects.filter(is_staff=False).count(), 1)

    @QuadeMock(managers)
    def test_execute_fixtures_with_kwargs(self):
        initial_user_count = User.objects.count()
        first_name = 'Baron'
        last_name = 'von Count'
        config = [('staff_user', {'first_name': first_name, 'last_name': last_name})]
        managers.manager.execute(config)
        self.assertEqual(User.objects.count(), initial_user_count + 1)
        # Get the newly created User.
        new_staff = User.objects.last()
        self.assertEqual(new_staff.first_name, first_name)
        self.assertEqual(new_staff.last_name, last_name)

    @QuadeMock(managers, funcs=[staff_user_id])
    def test_instructions_coerced_to_text(self):
        config = [('staff_user_id', {})]
        instructions = managers.manager.execute(config)
        self.assertEqual(instructions, '1')


class TestValidation(TestCase):

    @QuadeMock(managers)
    def test_validation_succeeds(self):
        good_function = 'staff_user'
        config = [(good_function, {})]
        managers.manager.validate(config)

    @QuadeMock(managers)
    def test_validation_fails(self):
        bad_function = 'does_not_exist'
        good_function = 'staff_user'
        config = [(bad_function, {}), (good_function, {})]
        with self.assertRaises(managers.ConfigurationError) as exc:
            managers.manager.validate(config)
        self.assertEqual(exc.exception.unregistered_functions, set([bad_function]))


class TestRegistration(TestCase):

    def test_register_method(self):
        self.assertEqual(managers.manager.registry, {})
        managers.manager.register(customer)
        self.assertEqual(managers.manager.registry, {'customer': customer})

    def test_register_decorator(self):
        self.assertEqual(managers.manager.registry, {})
        registered_func = managers.register(customer)
        self.assertEqual(managers.manager.registry, {'customer': registered_func})

    def tearDown(self):
        managers.manager._registry = {}
