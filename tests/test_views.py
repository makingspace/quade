from __future__ import absolute_import, division, print_function, unicode_literals

from django.contrib.auth import get_user_model
User = get_user_model()
try:
    from django.urls import reverse
except ImportError:
    from django.core.urlresolvers import reverse
from django_webtest import WebTest
from mock import mock

from quade import managers
from quade.models import QATestRecord

from .mock import QaMock
from . import factories


class TestViewPermissions(WebTest):

    def setUp(self):
        self.test_record = factories.QATestRecord()
        self.urls = [
            ('get', reverse('qa-main')),
            ('post', reverse('qa-main')),
            ('post', reverse('qa-mark-done', args=[self.test_record.id])),
        ]

    def test_superusers_can_access(self):
        superuser = factories.UserAdmin()
        self.app.set_user(superuser)
        for method, url in self.urls:
            resp = getattr(self.app, method)(url)
            # Follow up to one redirect
            if resp.status_code == 302:
                resp = resp.follow()
            self.assertEqual(resp.status_code, 200)

    def test_regular_users_cannot_access(self):
        user = factories.User()
        self.app.set_user(user)
        for method, url in self.urls:
            getattr(self.app, method)(url, status=403)

    def test_generic_staff_users_cannot_access(self):
        staff = factories.UserStaff()
        self.app.set_user(staff)
        for method, url in self.urls:
            getattr(self.app, method)(url, status=403)


class TestViews(WebTest):

    def setUp(self):
        self.superuser = factories.UserAdmin()
        self.app.set_user(self.superuser)

    @QaMock(managers)
    def test_execute(self):
        initial_count = QATestRecord.objects.count()
        initial_user_count = User.objects.count()
        factories.QATestScenario()  # Noise
        scenario2 = factories.QATestScenario(
            config=[('customer', {}), ('staff_user', {})]
        )
        url = reverse('qa-main')
        self.app.post(url, params={'scenarios': scenario2.slug})
        self.assertEqual(QATestRecord.objects.count(), initial_count + 1)
        new_record = QATestRecord.objects.last()
        self.assertEqual(new_record.created_by, self.superuser)
        self.assertEqual(new_record.scenario, scenario2)
        self.assertEqual(new_record.status, QATestRecord.Status.READY)
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
        # The record has set up the newly-created users as QAObjects.
        self.assertEqual(
            {obj.object for obj in new_record.qa_objects.all()}, {new_customer, new_staff}
        )

    @QaMock(managers)
    def test_execute_is_async(self):
        scenario = factories.QATestScenario(config=[('customer', {})])
        url = reverse('qa-main')
        with mock.patch('quade.views.execute_test_task') as mock_task:
            self.app.post(url, params={'scenarios': scenario.slug})
        new_record = QATestRecord.objects.last()
        mock_task.delay.assert_called_once_with(new_record.id)
        self.assertEqual(new_record.status, QATestRecord.Status.NOT_READY)

    def test_execute_without_test_scenario_defined(self):
        initial_count = QATestRecord.objects.count()
        url = reverse('qa-main')
        resp = self.app.post(url, params={'scenarios': 'nothing-exists-yet'})
        self.assertEqual(QATestRecord.objects.count(), initial_count)
        self.assertIn('Select a valid choice.', resp.text)

    def test_main_page_with_no_scenarios(self):
        url = reverse('qa-main')
        resp = self.app.get(url)
        self.assertIn('There are no test scenarios at this time.', resp.text)

    def test_mark_done(self):
        test_record = factories.QATestRecord()
        url = reverse('qa-mark-done', args=[test_record.id])
        self.app.post(url)
        test_record.refresh_from_db()
        self.assertEqual(test_record.status, QATestRecord.Status.DONE)
