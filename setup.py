#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import re
import sys

from setuptools import find_packages, setup


def get_version(*file_paths):
    """Retrieves the version."""
    filename = os.path.join(os.path.dirname(__file__), *file_paths)
    version_file = open(filename).read()
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError('Unable to find version string.')


version = get_version("src", "quade", "__init__.py")


if sys.argv[-1] == 'publish':
    try:
        import wheel
    except ImportError:
        print('Wheel library missing. Please run "pip install wheel"')
        sys.exit()
    try:
        import twine
    except ImportError:
        print('Twine library missing. Please run "pip install twine"')
        sys.exit()
    os.system('python setup.py sdist bdist_wheel --universal')
    os.system('twine upload dist/*')
    sys.exit()

if sys.argv[-1] == 'tag':
    print("Tagging the version on git:")
    os.system("git tag -a %s -m 'version %s'" % (version, version))
    os.system("git push --tags")
    sys.exit()

readme = open('README.rst').read()
# Replace relative internal reference to logo with an absolute external URL.
readme = readme.replace(
    'docs/_static/quade.*',
    'https://raw.githubusercontent.com/makingspace/quade/4ae3d090d36e2e8869c0edb50f6bede72446948d/docs/_static/quade_200x200.png',
)

history = open('HISTORY.rst').read().replace('.. :changelog:\n\n', '')

setup(
    name='quade',
    version=version,
    description="""The friendly QA tool for Django.""",
    long_description=readme + '\n\n' + history,
    author='Paul Baranay',
    author_email='pbaranay@makespace.com',
    url='https://github.com/makingspace/quade',
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    install_requires=["attrs", "django-fsm==1.6", "django-light-enums", "django_jinja", "future", "jsonfield"],
    extras_require={
        "celery": "celery"
    },
    license="MIT",
    zip_safe=False,
    keywords='django',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Framework :: Django',
        'Framework :: Django :: 1.8',
        'Framework :: Django :: 1.9',
        'Framework :: Django :: 1.10',
        'Framework :: Django :: 1.11',
        'Framework :: Django :: 2.0',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
)
