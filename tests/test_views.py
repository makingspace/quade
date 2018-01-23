from __future__ import absolute_import, division, print_function, unicode_literals

from django.contrib.auth import get_user_model
User = get_user_model()
from django.test import override_settings
try:
    from django.urls import reverse
except ImportError:
    from django.core.urlresolvers import reverse
from django_webtest import WebTest
from mock import mock

import quade
from quade import managers
from quade.models import Record

from .mock import QuadeMock
from .utils import requires_celery
from . import factories


class TestViewPermissionsBase(object):

    QUADE = None
    superuser_access = None
    staff_access = None
    user_access = None

    def setUp(self):
        self.test_record = factories.Record()
        self.urls = [
            ('get', reverse('quade-main')),
            ('post', reverse('quade-main')),
            ('post', reverse('quade-mark-done', args=[self.test_record.id])),
        ]

    def _access_checker(self, allowed):
        for method, url in self.urls:
            resp = getattr(self.app, method)(url, expect_errors=not allowed)
            # Follow up to one redirect
            if resp.status_code == 302:
                resp = resp.follow()
        return resp

    def check_access(self, allowed):
        expected_code = 200 if allowed else 403
        if getattr(self, 'QUADE'):
            with override_settings(QUADE=self.QUADE):
                resp = self._access_checker(allowed)
        else:
            resp = self._access_checker(allowed)

        self.assertEqual(resp.status_code, expected_code)

    def test_superuser(self):
        superuser = factories.UserAdmin()
        self.app.set_user(superuser)
        self.check_access(self.superuser_access)

    def test_staff(self):
        staff = factories.UserStaff()
        self.app.set_user(staff)
        self.check_access(self.staff_access)

    def test_regular_user(self):
        user = factories.User()
        self.app.set_user(user)
        self.check_access(self.user_access)


class TestDefaultViewPermissions(TestViewPermissionsBase, WebTest):

    superuser_access = True
    staff_access = False
    user_access = False


class TestCustomViewPermissions(TestViewPermissionsBase, WebTest):

    QUADE = quade.Settings(access_test_func=lambda self: self.request.user.is_staff)
    superuser_access = True
    staff_access = True
    user_access = False


class TestViews(WebTest):

    def setUp(self):
        self.superuser = factories.UserAdmin()
        self.app.set_user(self.superuser)

    @QuadeMock(managers)
    def test_execute(self):
        initial_count = Record.objects.count()
        initial_user_count = User.objects.count()
        factories.Scenario()  # Noise
        scenario2 = factories.Scenario(
            config=[('customer', {}), ('staff_user', {})]
        )
        url = reverse('quade-main')
        self.app.post(url, params={'scenarios': scenario2.slug})
        self.assertEqual(Record.objects.count(), initial_count + 1)
        new_record = Record.objects.last()
        self.assertEqual(new_record.created_by, self.superuser)
        self.assertEqual(new_record.scenario, scenario2)
        self.assertEqual(new_record.status, Record.Status.READY)
        self.assertEqual(User.objects.count(), initial_user_count + 2)
        # Get the newly created Users.
        new_customer = User.objects.filter(is_staff=False).last()
        new_staff = User.objects.filter(is_staff=True).last()
        self.assertEqual(
            new_record.instructions,
            '{} {}\n{} {}'.format(
                new_customer.first_name,
                new_customer.last_name,
                new_staff.first_name,
                new_staff.last_name,
            )
        )
        # The record has set up the newly-created users as RecordedObjects.
        self.assertEqual(
            {obj.object for obj in new_record.recorded_objects.all()}, {new_customer, new_staff}
        )

    @QuadeMock(managers)
    @requires_celery
    def test_execute_is_asynchronous_with_proper_setting(self):
        scenario = factories.Scenario(config=[('customer', {})])
        url = reverse('quade-main')
        qs = quade.Settings(use_celery=True)
        with mock.patch('quade.tasks.execute_test_task') as mock_task, override_settings(QUADE=qs):
            self.app.post(url, params={'scenarios': scenario.slug})
        new_record = Record.objects.last()
        mock_task.delay.assert_called_once_with(new_record.id)
        self.assertEqual(new_record.status, Record.Status.NOT_READY)

    def test_execute_without_test_scenario_defined(self):
        initial_count = Record.objects.count()
        url = reverse('quade-main')
        resp = self.app.post(url, params={'scenarios': 'nothing-exists-yet'})
        self.assertEqual(Record.objects.count(), initial_count)
        self.assertIn('Select a valid choice.', resp.text)

    def test_main_page_with_no_scenarios(self):
        url = reverse('quade-main')
        resp = self.app.get(url)
        self.assertIn('There are no test scenarios at this time.', resp.text)
        self.assertNotIn('form id="scenario-executor"', resp.text)

    def test_main_page_when_disabled(self):
        """When Quade is disabled, the main page shows a message to this effect."""
        qs = quade.Settings(allowed_envs=lambda _: False)
        with override_settings(QUADE=qs):
            url = reverse('quade-main')
            resp = self.app.get(url)
        self.assertIn('Quade has been disabled on this environment.', resp.text)
        self.assertNotIn('Execute', resp.text)

    @QuadeMock(managers)
    def test_main_page_when_use_celery_false(self):
        factories.Scenario(config=[('customer', {})])
        url = reverse('quade-main')
        qs = quade.Settings(use_celery=False, allowed_envs=quade.AllEnvs)
        with override_settings(QUADE=qs):
            resp = self.app.get(url)
        self.assertIn('To set up a new test, select a scenario to execute.', resp.text)
        self.assertNotIn('Your test will be created in a unready state', resp.text)

    @QuadeMock(managers)
    @requires_celery
    def test_main_page_when_use_celery_true(self):
        factories.Scenario(config=[('customer', {})])
        url = reverse('quade-main')
        qs = quade.Settings(use_celery=True, allowed_envs=quade.AllEnvs)
        with override_settings(QUADE=qs):
            resp = self.app.get(url)
        self.assertIn('To set up a new test, select a scenario to execute.', resp.text)
        self.assertIn('Your test will be created in a unready state', resp.text)

    def test_main_page_scenario_selector_when_disabled(self):
        """When Quade is disabled, the scenario selector is not shown."""
        factories.Scenario()
        qs = quade.Settings(allowed_envs=lambda _: False)
        with override_settings(QUADE=qs):
            url = reverse('quade-main')
            resp = self.app.get(url)
        self.assertNotIn('form id="scenario-executor"', resp.text)

    def test_mark_done(self):
        test_record = factories.Record()
        url = reverse('quade-mark-done', args=[test_record.id])
        self.app.post(url)
        test_record.refresh_from_db()
        self.assertEqual(test_record.status, Record.Status.DONE)
