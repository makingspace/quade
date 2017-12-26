from django.test import TestCase, override_settings

import quade


class TestModifyingDjangoSettings(object):

    allowed_envs = None
    active_on_debug = None
    active_on_staging = None
    active_on_prod = None

    def test_debug(self):
        with override_settings(DEBUG=True, ENV='testing', FOO='bar'):
            qs = quade.Settings(allowed_envs=self.allowed_envs)
            self.assertEqual(qs._modify_installed_apps(), self.active_on_debug)

    def test_staging(self):
        with override_settings(DEBUG=True, ENV='staging', FOO='bar'):
            qs = quade.Settings(allowed_envs=self.allowed_envs)
            self.assertEqual(qs._modify_installed_apps(), self.active_on_staging)

    def test_prod(self):
        with override_settings(DEBUG=False, ENV='prod', FOO='quux'):
            qs = quade.Settings(allowed_envs=self.allowed_envs)
            self.assertEqual(qs._modify_installed_apps(), self.active_on_prod)


class TestAllEnvs(TestModifyingDjangoSettings, TestCase):

    allowed_envs = quade.AllEnvs
    active_on_debug = True
    active_on_staging = True
    active_on_prod = True


class TestDebugEnvs(TestModifyingDjangoSettings, TestCase):

    allowed_envs = quade.DebugEnvs
    active_on_debug = True
    active_on_staging = True
    active_on_prod = False


class TestCallable(TestModifyingDjangoSettings, TestCase):

    @staticmethod
    def allowed_envs(s): return s.FOO == 'quux'

    active_on_debug = False
    active_on_staging = False
    active_on_prod = True


class TestIterable(TestModifyingDjangoSettings, TestCase):

    allowed_envs = ['testing', 'staging']
    active_on_debug = True
    active_on_staging = True
    active_on_prod = False

    def test_iterable(self):
        with override_settings(ENV='testing'):
            qs = quade.Settings(allowed_envs=['test', 'testing_2'])
            self.assertFalse(qs._modify_installed_apps())


class TestString(TestModifyingDjangoSettings, TestCase):

    allowed_envs = 'staging'
    active_on_debug = False
    active_on_staging = True
    active_on_prod = False

    def test_exactness_when_allowed_env_is_substring(self):
        with override_settings(ENV='testing'):
            qs = quade.Settings(allowed_envs='test')
            self.assertFalse(qs._modify_installed_apps())

    def test_exactness_when_django_env_is_substring(self):
        with override_settings(ENV='testing'):
            qs = quade.Settings(allowed_envs='testing_2')
            self.assertFalse(qs._modify_installed_apps())


class TestTypeError(TestCase):

    def test_type_error(self):
        with self.assertRaises(TypeError):
            quade.Settings(allowed_envs=42)


class TestSettings(TestCase):

    def test_uses_defaults(self):
        qs = quade.Settings()
        for setting in quade.settings.all_settings.values():
            self.assertEquals(getattr(qs, setting.name), setting.default)

    def test_load_fixtures(self):
        qs = quade.Settings(fixtures_file='tests.fixtures_registered')
        with override_settings(QUADE=qs):
            manager = quade.managers.manager
            manager.setup()
            self.assertEqual(set(manager.registry.keys()), {'registered_customer'})
        # Tear down: Reset the manager.
        manager._registry = {}

    def test_cannot_set_nonexistent_setting_singular(self):
        with self.assertRaises(AttributeError) as exc:
            quade.Settings(foo='bar')
        self.assertEqual(str(exc.exception), "No such setting: 'foo'")

    def test_cannot_set_nonexistent_setting_plural(self):
        with self.assertRaises(AttributeError) as exc:
            quade.Settings(foo='bar', baz='quux')
        self.assertRegexpMatches(
            str(exc.exception),
            "No such settings: ('foo', 'baz'|'baz', 'foo')"
        )

    def test_cannot_set_attributes_after_construction(self):
        qs = quade.Settings()
        with self.assertRaises(RuntimeError):
            qs.fixtures_file = 'my_module.fixtures'
