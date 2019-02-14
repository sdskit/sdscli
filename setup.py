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
    install_requires=['pyyaml', 'pygments', 'prompt-toolkit>=1.0,<2.0',
                      'fabric', 'tqdm==4.19.7', 'backoff'],
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
