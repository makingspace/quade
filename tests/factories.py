from factory import DjangoModelFactory, LazyAttribute, Sequence, SubFactory
from factory.fuzzy import FuzzyText

from django.contrib.auth import get_user_model

from quade import models as quade_models


# Factories for django.contrib.auth.User models


class User(DjangoModelFactory):

    class Meta:
        model = get_user_model()

    username = Sequence(lambda n: 'factory_user_{}'.format(n))
    first_name = 'Factory'
    last_name = Sequence(lambda n: 'User {}'.format(n))
    email = LazyAttribute(lambda obj: '{}@example.com'.format(obj))


class UserStaff(User):

    is_staff = True


class UserAdmin(User):

    is_staff = True
    is_superuser = True


# Factories for Quade models


class QATestScenario(DjangoModelFactory):

    class Meta:
        model = quade_models.QATestScenario

    slug = Sequence(lambda n: 'scenario-{}'.format(n))
    description = FuzzyText(length=15)


class QATestRecord(DjangoModelFactory):

    class Meta:
        model = quade_models.QATestRecord

    scenario = SubFactory(QATestScenario)
    created_by = SubFactory(UserAdmin)


class QAObject(DjangoModelFactory):

    class Meta:
        model = quade_models.QAObject

    object = SubFactory(User)
    record = SubFactory(QATestRecord)
