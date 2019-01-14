#!/usr/bin/env python
import os
import setuptools


PROJECT_ROOT = os.path.dirname(os.path.realpath(__file__))


def read_requirements(fn):
    requirements = []
    with open(os.path.join(PROJECT_ROOT, fn)) as f:
        for line in f:
            line = line.strip()

            if not line or line.startswith('#') or line.startswith('-e'):
                continue

            requirements.append(line)
    return requirements


setuptools.setup(
    name='falcon_sessions',
    use_scm_version=True,
    description='Sessions support for Falcon web framework',
    author='Ingate Development Team',
    author_email='idev.tech@ingate.ru',
    url='https://www.ingate.ru/',
    packages=setuptools.find_packages(exclude=('tests', 'tests.*')),
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=read_requirements('requirements.txt'),
    setup_requires=['setuptools_scm'],
    extras_require={
        'redis': read_requirements('requirements-redis.txt')
    },
)
