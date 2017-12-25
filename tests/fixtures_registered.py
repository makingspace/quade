from __future__ import absolute_import, division, print_function, unicode_literals

from quade.managers import register

from .fixtures import customer


@register
def registered_customer():
    return customer()
