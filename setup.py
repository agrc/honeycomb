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
    packages=['honeycomb'],
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
        'docopt==0.6.2'
    ],
    dependency_links=[
    ],
    extras_require={
        'test': [
            'pytest',
            'pytest-watch',
            'pytest-cov',
            'pytest-flake8'
        ]
    },
    entry_points={
        "console_scripts": [
            "honeycomb = honeycomb.__main__:main"
        ]
    }
)
