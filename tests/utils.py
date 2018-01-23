import os
import unittest


def requires_celery(func):
    return unittest.skipUnless(os.getenv("TEST_CELERY"), "Requires Celery")(func)
