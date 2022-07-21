from setuptools import setup

setup(
    name="honeycomb",
    version="1.3.0",
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
        "Programming Language :: Python :: 3.7",
        "Topic :: Utilities"
    ],
    keywords=[
    ],
    install_requires=[
        'arcgis>=2',
        'colorama>=0',
        'docopt>=0',
        'google-cloud-storage>=2',
        'humanize>=4',
        'p_tqdm>=1',
        'pygsheets>=2',
        'requests>=2',
        'tabulate>=0',
        'tqdm>=4'
    ],
    dependency_links=[
    ],
    extras_require={
        'test': [
            'flake8',
            'mock',
            'pytest-benchmark',
            'pytest-cov',
            'pytest-env',
            'pytest-flake8==1.0.0',
            'pytest-watch',
            'pytest',
            'requests_mock'
        ]
    },
    entry_points={
        "console_scripts": [
            "honeycomb = honeycomb.__main__:main"
        ]
    }
)
