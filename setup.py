import setuptools
from machine_common_sense import _version as version

with open('README.md', 'r') as readme_file:
    long_description = readme_file.read()


setuptools.setup(
    name='mcs_ingest',
    version=version.__version__,
    maintainer='Next Century, a wholly owned subsidiary of CACI',
    maintainer_email='mcs-ta2@machinecommonsense.com',
    url='https://github.com/NextCenturyCorporation/mcs-ingest/',
    description=('Machine Common Sense Data Ingest and Scoring Pipeline'),
    long_description=long_description,
    long_description_content_type='text/markdown',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
    ],
    license='Apache-2',
    python_requires=">=3.8",
    packages=setuptools.find_packages(),
    install_requires=[
        'machine-common-sense>=0.4.6',
        'pymongo>=3.11.3',
        'flake8>=3.8.4',
        'numpy>=1.19.4',
        'pandas>=1.2.3'
    ]
)
