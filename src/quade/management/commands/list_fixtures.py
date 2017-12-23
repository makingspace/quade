from __future__ import absolute_import, division, print_function, unicode_literals

from django.core.management.base import BaseCommand

from quade.managers import manager


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        if len(manager.registry) == 0:
            self.stdout.write("0 functions are registered with Quade.")
        else:
            if len(manager.registry) == 1:
                opening = "1 function is"
            else:
                opening = "{} functions are".format(len(manager.registry))
            self.stdout.write("{} registered with Quade:".format(opening))
            for func_name in sorted(manager.registry):
                self.stdout.write("- {}".format(func_name))
