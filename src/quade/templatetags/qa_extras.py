from django_jinja import library


@library.filter
def status(record):
    return record.get_status_display().replace('_', ' ').title()
