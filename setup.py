from setuptools import setup

from awsdsc import __version__ as version

with open("./requirements.txt", "r") as f:
    requirements = f.readlines()


setup(
    name="awsdsc",
    version=version,
    description="AWS universal describe command",
    author="Takatoshi Iwasa",
    author_email="Takatoshi.Iwasa@jp.nttdata.com",
    packages=["awsdsc"],
    entry_points={
        "console_scripts": [
            "awsdsc = awsdsc.main:main",
        ],
    },
    include_package_data=True,
    install_requires=requirements,
)
