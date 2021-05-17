"""Distribution settings."""

import pathlib

from setuptools import setup


HERE = pathlib.Path(__file__).parent
README = (HERE / "README.md").read_text()
REQUIREMENTS = (HERE / "requirements.txt").read_text().splitlines()

setup(
    name="truffleHog3",
    version="2.0.5",
    packages=["truffleHog3", "truffleHog3.lib"],
    license="GNU",
    description="Find secrets in your codebase.",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/feeltheajf/truffleHog3",
    author="Ilya Radostev",
    author_email="feeltheajf@gmail.com",
    include_package_data=True,
    python_requires=">=3.6",
    install_requires=REQUIREMENTS,
    entry_points={"console_scripts": ["trufflehog3 = truffleHog3.cli:run"]},
)
