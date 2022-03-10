from setuptools import setup
from pathlib import Path

from awsdsc import __version__ as version

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")
requirements = (this_directory / "requirements.txt").read_text(encoding="utf-8")

setup(
    name="awsdsc",
    version=version,
    description="AWS universal describe command",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Takatoshi Iwasa",
    author_email="Takatoshi.Iwasa@jp.nttdata.com",
    packages=["awsdsc"],
    entry_points={
        "console_scripts": [
            "awsdsc = awsdsc.main:main",
        ],
    },
    include_package_data=True,
    install_requires=requirements.splitlines(),
)
