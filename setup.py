from setuptools import setup, find_packages
from importlib.metadata import entry_points
import pathlib

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

# The text of the README file
REQUIRE = (HERE / "requirements.txt").read_text()

setup(
    name="pquisby",
    version="0.0.2",
    description="Quisby is a data processing and visualization tool for benchmark testing.",
    url = 'https://github.com/sousinha1997/Quisby',
    author = 'Soumya Sinha',
    author_email = 'sinhasoumya97@gmail.com',
    license = 'GPL v3.0',
    packages=find_packages("src"),
    package_dir={"":"src"},
    long_description=README,
    long_description_content_type="text/markdown",
    install_requires = REQUIRE,
    entry_points={
        "console_scripts": [
            "pquisby = pquisby.command.main:main",
        ]
    },
    include_package_data=True,
)