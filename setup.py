import glob
from os.path import basename
from os.path import splitext

from setuptools import find_packages
from setuptools import setup


setup(
    name="honeycomb",
    version="0.0.0",
    license="MIT",
    description="CLI tool for managing AGRC base map caches (vector & raster).",
    long_description="",
    author="Scott Davis",
    author_email="stdavis@utah.gov",
    url="https://github.com/agrc/honeycomb",
    packages=find_packages("src"),
    package_dir={"": "src"},
    py_modules=[splitext(basename(i))[0] for i in glob.glob("src/*.py")],
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Unix",
        "Operating System :: POSIX",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Topic :: Utilities"
    ],
    keywords=[
    ],
    install_requires=[
        'colorama==0.3.7',
        'docopt==0.6.2',
        #: pyopenssl, ndg-httpsclient, pyasn1 are there to disable ssl warnings in requests
    ],
    dependency_links=[
    ],
    extras_require={
    },
    entry_points={
        "console_scripts": [
            "honeycomb = honeycomb.__main__:main"
        ]
    }
)
