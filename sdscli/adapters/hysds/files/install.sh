#!/bin/bash
BASE_PATH=$(dirname "${BASH_SOURCE}")
BASE_PATH=$(cd "${BASE_PATH}"; pwd)

source $HOME/verdi/bin/activate

# move code
#mv $BASE_PATH/<some_code> $HOME/

# update rpm
#sudo yum remove -y some_package
#sudo yum install -y $BASE_PATH/some_package-*.rpm

# install python packages
cd $BASE_PATH/prov_es
pip install -e .
cd $BASE_PATH/osaka
pip install -e .
cd $BASE_PATH/hysds_commons
pip install -e .
cd $BASE_PATH/hysds/third_party/celery-v3.1.25.pqueue
pip install -e .
cd $BASE_PATH/hysds
pip install -e .
cd $BASE_PATH/sciflo
pip install -e .

# copy hysds configs
rm -rf $HOME/verdi/etc
cp -rp $BASE_PATH/etc $HOME/verdi/etc
cp -rp $HOME/verdi/ops/hysds/celeryconfig.py $HOME/verdi/etc/

# write supervisord from template
IPADDRESS_ETH0=$(/usr/sbin/ifconfig $(/usr/sbin/route | awk '/default/{print $NF}') | grep 'inet ' | sed 's/addr://' | awk '{print $2}') 
#FQDN=$(python -c "import socket; print socket.getfqdn()")
FQDN=$IPADDRESS_ETH0
sed "s/__IPADDRESS_ETH0__/$IPADDRESS_ETH0/g" $HOME/verdi/etc/supervisord.conf.tmpl | \
  sed "s/__FQDN__/$FQDN/g" > $HOME/verdi/etc/supervisord.conf

# move ariamh and tropmap
#rm -rf $HOME/ariamh $HOME/tropmap
#mv -f $BASE_PATH/ariamh $HOME/
#mv -f $BASE_PATH/tropmap $HOME/

# move creds
rm -rf $HOME/.aws
mv -f $BASE_PATH/creds/.aws $HOME/
rm -rf $HOME/.boto; mv -f $BASE_PATH/creds/.boto $HOME/
rm -rf $HOME/.s3cfg; mv -f $BASE_PATH/creds/.s3cfg $HOME/
rm -rf $HOME/.netrc; mv -f $BASE_PATH/creds/.netrc $HOME/; chmod 600 $HOME/.netrc

# extract beefed autoindex
cd /data/work
tar xvfj $BASE_PATH/beefed-autoindex-open_in_new_win.tbz2

# prime verdi docker image
export AWS_ACCESS_KEY_ID="$(grep aws_access_key_id $HOME/.aws/credentials | head -1 | cut -d= -f 2 | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
export AWS_SECRET_ACCESS_KEY="$(grep aws_secret_access_key $HOME/.aws/credentials | head -1 | cut -d= -f 2 | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
export VERDI_PRIMER_IMAGE="{{ VERDI_PRIMER_IMAGE }}"
export VERDI_PRIMER_IMAGE_BASENAME="$(basename $VERDI_PRIMER_IMAGE 2>/dev/null)"
rm -rf /tmp/${VERDI_PRIMER_IMAGE_BASENAME}
aws s3 cp ${VERDI_PRIMER_IMAGE} /tmp/${VERDI_PRIMER_IMAGE_BASENAME}
docker load -i /tmp/${VERDI_PRIMER_IMAGE_BASENAME}
docker tag hysds/verdi:{{ VERDI_TAG }} hysds/verdi:latest
