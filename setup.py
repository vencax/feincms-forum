#!/usr/bin/env python
from setuptools import setup, find_packages
import os

README_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'README')

description = 'vxkforum simple, modular, easily integrated forum for Django based sites.'

if os.path.exists(README_PATH):
    long_description = open(README_PATH).read()
else:
    long_description = description

setup(name='django-vxk-forum',
    version='',
    description=description,
    license='BSD',
    url='https://github.com/vencax/django-vxk-forum',
    author='vencax',
    author_email='vencax@centrum.cz',
    packages=find_packages(),
    install_requires=[
        'django>=1.3',
        'django-haystack',
        'south',
        'postmarkup',
        'setuptools',
        'typogrify',
        'django-ckeditor',
        'django-gravatar',
    ],
    keywords="django forum bb",
    include_package_data=True,
)
