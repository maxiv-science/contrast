import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="contrast",
    version="0.0.1",
    author="Alexander Bjorling",
    author_email="alexander.bjorling@maxiv.lu.se",
    description="Light weight data acquisition framework for orchestrating beamline experiments.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/alexbjorling/contrast",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    include_package_data=True,
)
