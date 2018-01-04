from django.core.management import call_command
from django.test import TestCase
from django.utils.six import StringIO

from quade import managers
from .mock import QuadeMock
from .fixtures import customer


class TestListFixturesCommand(TestCase):

    command_name = 'list_fixtures'

    def setUp(self):
        self.out = StringIO()

    def test_zero_fixtures(self):
        call_command(self.command_name, stdout=self.out)
        self.assertEqual(self.out.getvalue(), "0 functions are registered with Quade.\n")

    @QuadeMock(managers, funcs=[customer])
    def test_one_fixture(self):
        call_command(self.command_name, stdout=self.out)
        output = self.out.getvalue().split('\n')
        self.assertEqual(len(output), 3)
        self.assertEqual(output[0], "1 function is registered with Quade:")
        self.assertEqual(output[1], "- customer")
        self.assertEqual(output[2], "")

    @QuadeMock(managers)
    def test_two_fixtures(self):
        call_command(self.command_name, stdout=self.out)
        output = self.out.getvalue().split('\n')
        self.assertEqual(len(output), 4)
        self.assertEqual(output[0], "2 functions are registered with Quade:")
        self.assertEqual(output[1], "- customer")
        self.assertEqual(output[2], "- staff_user")
        self.assertEqual(output[3], "")
