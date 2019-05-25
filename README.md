# sdscli
Command line interface for SDSKit


## Prerequisites

- python 3.7+
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
  pip install -r requirements.txt
  pip install .
  ```

## Create cluster

1. Populate SDS configuration:
  ```
  sds configure
  ```

2. Initialize SDS subsystem components:
  ```
  sds orch init all
  ```

3. Start SDS:
  ```
  sds orch start all
  ```

4. Stop SDS:
  ```
  sds orch stop all
  ```

## Usage
```
usage: sds [-h] [--debug]
           {configure,update,kibana,ship,start_tps,stop_tps,start,stop,reset,status,ci,pkg,cloud,rules,job,orch}
           ...

SDSKit command line interface.

positional arguments:
  {configure,update,kibana,ship,start_tps,stop_tps,start,stop,reset,status,ci,pkg,cloud,rules,job,orch}
                        Functions
    configure           configure SDS config file
    update              update SDS components
    kibana              update SDS components
    ship                ship verdi code/config bundle
    start_tps           start TPS on SDS components
    stop_tps            stop TPS on SDS components
    start               start SDS components
    stop                stop SDS components
    reset               reset SDS components
    status              status of SDS components
    ci                  configure continuous integration for SDS cluster
    pkg                 SDS package management
    cloud               SDS cloud management
    rules               SDS user rules management
    job                 SDS job subcommand
    update              update SDS components
    orch                SDS container orchestration

optional arguments:
  -h, --help            show this help message and exit
  --debug, -d           turn on debugging
```
