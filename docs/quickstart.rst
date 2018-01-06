Quickstart
==========

1. Follow the :doc:`installation guide </installation>`:

  .. include:: installation_steps.rst

2. Create a fixtures file, ``fixtures.py``, in the root of your project::

    # fixtures.py

    import uuid

    from django.contrib.auth import get_user_model

    from quade.managers import register


    User = get_user_model()


    @register
    def user():
        new_user = User.objects.create(
            first_name='Alyssa',
            last_name='Hacker',
            username='alyssa-{}'.format(uuid.uuid4())
        )
        return "User #{}".format(new_user.pk)

3. Update your settings to make Quade aware of your fixtures file::

    QUADE = quade.settings(fixtures_file='fixtures')

4. Enter the Django shell and create a :class:`.Scenario` that uses this fixture::

    from quade.models import Scenario
    Scenario.objects.create(
        config=[('user', {})],
        description='Single User',
        slug='single-user',
        status=Scenario.Status.ACTIVE
    )

5. Start your project's webserver and visit the main Quade page. You will be able to generate new
   users on demand by selecting the "Single User" scenario and executing it.

6. Begin creating your own fixtures and :class:`Scenarios <.Scenario>`!
