import os.path
from setuptools import setup

with open(os.path.join(os.path.dirname(__file__), "README.md")) as fp:
    long_description = fp.read()

setup(
    name="amdgpu-fan-ctrl",
    description="AMD GPU fan control for Linux",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/luismsgomes/amdgpu-fan-ctrl",
    author="Luís Gomes",
    author_email="luismsgomes@gmail.com",
    version="0.0.2",
    package_dir={"": "."},
    py_modules=["amdgpu_fan_ctrl"],
    license="MIT",
    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
    ],
)
