__all__ = ['UserPassesTestMixin']


try:
    from django.contrib.auth.mixins import UserPassesTestMixin
except ImportError:  # pragma: no cover
    # Backport from Django 1.9.
    from django.conf import settings
    from django.contrib.auth.views import redirect_to_login
    from django.core.exceptions import ImproperlyConfigured, PermissionDenied
    from django.utils.encoding import force_text
    REDIRECT_FIELD_NAME = 'next'

    class AccessMixin(object):
        """
        Abstract CBV mixin that gives access mixins the same customizable
        functionality.
        """
        login_url = None
        permission_denied_message = ''
        raise_exception = False
        redirect_field_name = REDIRECT_FIELD_NAME

        def get_login_url(self):
            """
            Override this method to override the login_url attribute.
            """
            login_url = self.login_url or settings.LOGIN_URL
            if not login_url:
                raise ImproperlyConfigured(
                    '{0} is missing the login_url attribute. Define {0}.login_url, settings.LOGIN_URL, or override '
                    '{0}.get_login_url().'.format(self.__class__.__name__)
                )
            return force_text(login_url)

        def get_permission_denied_message(self):
            """
            Override this method to override the permission_denied_message attribute.
            """
            return self.permission_denied_message

        def get_redirect_field_name(self):
            """
            Override this method to override the redirect_field_name attribute.
            """
            return self.redirect_field_name

        def handle_no_permission(self):
            if self.raise_exception:
                raise PermissionDenied(self.get_permission_denied_message())
            return redirect_to_login(self.request.get_full_path(), self.get_login_url(),
                                     self.get_redirect_field_name())

    class UserPassesTestMixin(AccessMixin):
        """
        CBV Mixin that allows you to define a test function which must return True
        if the current user can access the view.
        """

        def test_func(self):
            raise NotImplementedError(
                '{0} is missing the implementation of the test_func() method.'.format(
                    self.__class__.__name__)
            )

        def get_test_func(self):
            """
            Override this method to use a different test_func method.
            """
            return self.test_func

        def dispatch(self, request, *args, **kwargs):
            user_test_result = self.get_test_func()()
            if not user_test_result:
                return self.handle_no_permission()
            return super(UserPassesTestMixin, self).dispatch(request, *args, **kwargs)
