#!/usr/bin/env python
from setuptools import find_packages, setup

from push2rb import get_package_version


PACKAGE_NAME = "push2rb"


setup(
    name=PACKAGE_NAME,
    version=get_package_version(),
    license="MIT",
    description="Repository hooks for pushing code to Review Board",
    packages=find_packages(),
    install_requires=[
        'mercurial>=3.0.1',
        'RBTools>=0.6.0',
    ],
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
    ],
)
