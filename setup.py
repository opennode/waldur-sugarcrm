#!/usr/bin/env python

from setuptools import setup, find_packages


install_requires = [
    'nodeconductor>=0.76.0',
    'sugarcrm>=0.1.1',
]


setup(
    name='nodeconductor-sugarcrm',
    version='0.1.0',
    author='OpenNode Team',
    author_email='info@opennodecloud.com',
    url='http://nodeconductor.com',
    description='NodeConductor SugarCRM adds SugarCRM support to NodeConductor',
    long_description=open('README.rst').read(),
    package_dir={'': 'src'},
    packages=find_packages('src', exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    install_requires=install_requires,
    zip_safe=False,
    # extras_require={
    #     'test': tests_requires,
    #     'dev': dev_requires,
    # },
    entry_points={
        'nodeconductor_extensions': (
            'nodeconductor_sugarcrm = nodeconductor_sugarcrm.urls',
        ),
    },
    # tests_require=tests_requires,
    include_package_data=True,
    classifiers=[
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Operating System :: OS Independent',
        'License :: Other/Proprietary License',
    ],
)
