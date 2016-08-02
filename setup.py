#!/usr/bin/env python
from setuptools import setup, find_packages, Command
from setuptools.command.test import test

import os, sys, subprocess

class TestCommand(Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        raise SystemExit(
            subprocess.call([sys.executable,
                             'app_test_runner.py',
                             'test_project']))

install_requires = [
    'django-dirtyfield>=0.9',
    'six',
    'Django>=1.8',
    'diff-match-patch>=20121119',
    'django-extended-choices>=1.0.6',
    'django-current-request>=0.1',
    ]
base_dir = os.path.dirname(os.path.abspath(__file__))

setup(
    name = "django-history",
    version = "0.5",
    description = "History for Django ORM data changes",
    url = "http://github.com/futurice/django-history",
    author = "Jussi Vaihia",
    author_email = "jussi.vaihia@futurice.com",
    packages = ["djangohistory"],
    include_package_data = True,
    keywords = 'django model history undo',
    license = 'BSD',
    install_requires = install_requires,
    cmdclass = {
        'test': TestCommand,
    },
)
