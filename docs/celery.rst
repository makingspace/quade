Using Celery
============

By default, Quade will execute :class:`Records <.Record>` synchronously.
If you wish to execute them asynchronously instead,
Quade ships with a Celery task for this purpose.
To enable it, specify `use_celery=True` in your Quade :doc:`setting <settings>`.

You must also ensure that Celery is installed and
:doc:`properly configured <celery:django/first-steps-with-django>`.
You can install Celery as a dependency of Quade by specifying the celery extra
during installation::

  pip install quade[celery]
