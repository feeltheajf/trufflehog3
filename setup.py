"""Distribution settings."""

from setuptools import setup

setup(
    name="truffleHog3",
    version="0.1.0",
    description="Find secrets in your codebase.",
    url="https://github.com/feeltheajf/truffleHog",
    author="Ilya Radostev",
    author_email="feeltheajf@gmail.com",
    license="GNU",
    packages=["truffleHog3"],
    install_requires=[
        "GitPython == 2.1.1",
    ],
    entry_points={
      "console_scripts": ["trufflehog = truffleHog:main"],
    },
)
