#!/usr/bin/env python
import sys
from setuptools import setup, find_packages


dev_requires = [
    'Sphinx==1.2.2',
]

tests_require = [
    'factory_boy==2.4.1',
    'django-celery==3.1.16',
    'mock==1.0.1',
    'mock-django==0.6.6',
    'six>=1.9.0',
]

install_requires = [
    'nodeconductor>0.102.2',
    'nodeconductor_openstack>=0.4.1',
    'sugarcrm>=0.1.1',
]

setup(
    name='nodeconductor-sugarcrm',
    version='0.3.0',
    author='OpenNode Team',
    author_email='info@opennodecloud.com',
    url='http://nodeconductor.com',
    description='NodeConductor SugarCRM adds SugarCRM support to NodeConductor',
    long_description=open('README.rst').read(),
    package_dir={'': 'src'},
    packages=find_packages('src', exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    install_requires=install_requires,
    zip_safe=False,
    extras_require={
        'dev': dev_requires,
    },
    entry_points={
        'nodeconductor_extensions': (
            'nodeconductor_sugarcrm = nodeconductor_sugarcrm.extension:SugarCRMExtension',
        ),
    },
    # tests_require=tests_requires,
    include_package_data=True,
    classifiers=[
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: Apache Software License',
    ],
)
