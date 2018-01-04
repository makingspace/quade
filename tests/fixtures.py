from __future__ import absolute_import, division, print_function, unicode_literals

from tests import factories


# Fixtures in this file are NOT decorated with @register because their registration is handled
# by being mocked; see tests.mock.


def customer():
    """The simplest possible fixture."""
    customer = factories.User()
    return ' '.join([customer.first_name, customer.last_name])


def staff_user(**kwargs):
    staff = factories.UserStaff(**kwargs)
    return ' '.join([staff.first_name, staff.last_name])
