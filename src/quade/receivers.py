from __future__ import absolute_import, division, print_function, unicode_literals

from contextlib import contextmanager
from functools import partial

from django.db.models.signals import post_save


def associate_instance_with_qa_record(record, instance, created, **kwargs):
    """
    A signal receiver that's meant to catch a post-save signal and associate a created model
    instance with the QATestRecord that generated it. Can only be used as a signal when the `record`
    argument is fixed (via functools.partial).
    """
    from .models import QAObject
    if created and not isinstance(instance, QAObject):  # Avoid infinite recursion
        QAObject.objects.create(record=record, object=instance)


@contextmanager
def connect_qa_object_receiver(record):
    """
    A context manager that connects the post-save signal to the associate_instance_with_qa_record
    receiver, and ensures the receiver is disconnected on exit.
    """
    callback = partial(associate_instance_with_qa_record, record=record)
    post_save.connect(callback)
    yield callback
    post_save.disconnect(callback)
