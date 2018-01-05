#. Install Quade with pip::

    pip install quade

#. Add Quade to your project's ``INSTALLED_APPS``::

    INSTALLED_APPS = [
        ...
        'quade.apps.QuadeConfig',
    ]

#. Initialize the Quade settings by adding these lines to your Django settings::

    import quade

    QUADE = quade.Settings()

  (By default, Quade will only be available when ``DEBUG=True``. For more
  details, see :doc:`settings`.)

4. Add the `django_jinja`_ template handler to your ``TEMPLATES`` setting,
   while retaining any other template handlers you have. For example::

    TEMPLATES = [
        # Existing code, leave in-place
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            ...
        },
        # New code to add
        {
            'BACKEND': 'django_jinja.backend.Jinja2',
            'DIRS': [],
            'APP_DIRS': True,
            'OPTIONS': {
                'app_dirname': 'jinja2',
            },
        },
    ]

#. Add Quade to your URL configuration, e.g.::

    # urls.py

    urlpatterns = [
        ...
        url(r'^quade/', include('quade.urls'))
    ]

#. Run migrations::

    python manage.py migrate quade

.. _django_jinja: https://niwinz.github.io/django-jinja/latest/