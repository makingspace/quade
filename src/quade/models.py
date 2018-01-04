from __future__ import absolute_import, division, print_function, unicode_literals

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models as m
from django.utils.encoding import python_2_unicode_compatible
from django_fsm.db.fields import FSMIntegerField, transition
from django_light_enums import enum
from jsonfield import JSONField

from .managers import manager, ConfigurationError
from .receivers import connect_qa_object_receiver


class ScenarioManager(m.QuerySet):

    def active(self):
        return self.filter(status=Scenario.Status.ACTIVE)


@python_2_unicode_compatible
class Scenario(m.Model):
    """
    A specific scenario that QA tests will be run against.
    """

    class Meta:
        app_label = 'quade'
        ordering = ['description']

    class Status(enum.Enum):
        INACTIVE = 0
        ACTIVE = 10

    objects = ScenarioManager.as_manager()

    REGISTRY = {}

    slug = m.SlugField(unique=True)
    status = enum.EnumField(Status, default=Status.ACTIVE)
    config = JSONField()
    description = m.TextField()
    created_on = m.DateTimeField(auto_now_add=True)
    updated_on = m.DateTimeField(auto_now=True)

    def __str__(self):
        return '#{}: {}'.format(self.id, self.description)

    def activate(self):
        self.status = self.Status.ACTIVE
        self.save()

    def deactivate(self):
        self.status = self.Status.INACTIVE
        self.save()

    def delete(self):
        self.deactivate()

    def hard_delete(self, *args, **kwargs):
        super(Scenario, self).delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        try:
            manager.validate(self.config)
        except ConfigurationError as exc:
            raise ValidationError("config {} contains unregistered function(s): {}".format(
                self.config, ','.join(exc.unregistered_functions)
            ))
        super(Scenario, self).save(*args, **kwargs)


class Record(m.Model):
    """
    A record of setting up, and possibly executing, a particular test scenario.
    """

    class Meta:
        app_label = 'quade'

    class Status(enum.Enum):
        FAILED = -10
        NOT_READY = -1
        READY = 1  # Django-FSM doesn't work well with 0, because it evaluates as falsey.
        IN_PROGRESS = 10
        DONE = 20

    scenario = m.ForeignKey(Scenario, on_delete=m.PROTECT)
    instructions = m.TextField(
        blank=True,
        null=True,
        help_text="Information needed to run this particular scenario, such as usernames and login"
        " information."
    )
    status = FSMIntegerField(choices=Status.choices, default=Status.NOT_READY)
    created_by = m.ForeignKey(settings.AUTH_USER_MODEL, related_name='+', on_delete=m.PROTECT)
    created_on = m.DateTimeField(auto_now_add=True)
    updated_on = m.DateTimeField(auto_now=True)

    def execute_test(self):
        """
        Public method for attempting to execute a test scenario. Exceptions put the record in the
        FAILED state and re-raise.
        """
        try:
            self._execute()
        except Exception as ex:
            self._fail(exception=ex)
            raise

    @transition(status, source=Status.NOT_READY, target=Status.READY, save=True)
    def _execute(self):
        with connect_qa_object_receiver(self):
            instructions = manager.create(self.scenario.config)
        self.instructions = instructions

    @transition(status, source=Status.NOT_READY, target=Status.FAILED, save=True)
    def _fail(self, exception):
        self.instructions = repr(exception)


@python_2_unicode_compatible
class RecordedObject(m.Model):
    """
    A joiner table for creating a generic many-to-many relation between Records and any other
    objects.
    """

    class Meta:
        app_label = 'quade'

    content_type = m.ForeignKey(ContentType, on_delete=m.CASCADE)
    object_id = m.PositiveIntegerField()
    object = GenericForeignKey('content_type', 'object_id')
    record = m.ForeignKey(Record, related_name='recorded_objects', on_delete=m.CASCADE)

    def __str__(self):
        return "RecordedObject #{}: {}".format(self.pk, self.object)
