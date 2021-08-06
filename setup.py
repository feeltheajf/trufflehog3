"""Distribution settings."""

from pathlib import Path
from setuptools import setup

from trufflehog3 import __NAME__, __VERSION__

HERE = Path(__file__).parent
README = (HERE / "README.md").read_text()
REQUIREMENTS = (HERE / "requirements.txt").read_text().splitlines()

setup(
    name=__NAME__,
    version=__VERSION__,
    packages=[__NAME__],
    license="GNU",
    description="Find secrets in your codebase",
    long_description=README,
    long_description_content_type="text/markdown",
    url=f"https://github.com/feeltheajf/{__NAME__}",
    author="Ilya Radostev",
    author_email="feeltheajf@gmail.com",
    include_package_data=True,
    python_requires=">=3.7",
    install_requires=REQUIREMENTS,
    entry_points={"console_scripts": [f"{__NAME__} = {__NAME__}.cli:run"]},
)
