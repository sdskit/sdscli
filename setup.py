from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from setuptools import setup, find_packages
import sdscli


setup(
    name='sdscli',
    version=sdscli.__version__,
    long_description=sdscli.__description__,
    url=sdscli.__url__,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=['PyYAML>=5.1', 'Pygments>=2.4.0', 'prompt-toolkit==1.0.16',
                      'tqdm>=4.32.1', 'backoff>=1.8.0', 'future>=0.17.1', 'requests>=2.22.0',
                      'kombu>=4.5.0', 'redis>=3.2.1', 'elasticsearch>=1.0.0,<2.0.0', 'boto3>=1.9.154',
                      'fabric3>=1.14.post1', 'Jinja2>=2.10.1'],
    entry_points={
        'console_scripts': [
            'sds=sdscli.command_line:main'
        ]
    },
    package_data={
        '': ['adapters/hysds/files/*', 'adapters/hysds/files/*/*',
             'adapters/sdskit/files/*', 'adapters/sdskit/files/*/*'],
    }
)
