# sdscli
Command line interface for SDSKit


## Prerequisites

- pip 9.0.1+
- setuptools 36.0.1+
- virtualenv 1.10.1+


## Installation

1. Create virtual environment and activate:
  ```
  virtualenv env
  source env/bin/activate
  ```

2. Update pip and setuptools:
  ```
  pip install -U pip
  pip install -U setuptools
  ```

3. Install sdscli:
  ```
  git clone https://github.com/sdskit/sdscli.git
  cd sdscli
  pip install .
  ```

## Usage
```
usage: sds [-h] [--debug]
           
           {configure,update,ship,start,stop,reset,status,ci,pkg,cloud,rules,job}
           ...

SDSKit command line interface.

positional arguments:
  {configure,update,ship,start,stop,reset,status,ci,pkg,cloud,rules,job}
                        Functions
    configure           configure SDS config file
    update              update SDS components
    ship                ship verdi code/config bundle
    start               start SDS components
    stop                stop SDS components
    reset               reset SDS components
    status              status of SDS components
    ci                  configure continuous integration for SDS cluster
    pkg                 SDS package management
    cloud               SDS cloud management
    rules               SDS user rules management
    job                 SDS job subcommand

optional arguments:
  -h, --help            show this help message and exit
  --debug, -d           turn on debugging
```
