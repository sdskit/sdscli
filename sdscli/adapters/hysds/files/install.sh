#!/bin/bash
BASE_PATH=$(dirname "${BASH_SOURCE}")
BASE_PATH=$(cd "${BASE_PATH}"; pwd)

source $HOME/verdi/bin/activate

# copy hysds configs
rm -rf $HOME/verdi/etc
cp -rp $BASE_PATH/etc $HOME/verdi/etc
cp -rp $HOME/verdi/ops/hysds/celeryconfig.py $HOME/verdi/etc/

# detect GPUs/NVIDIA driver configuration
GPUS=0
if [ -e "/usr/bin/nvidia-smi" ]; then
  NVIDIA_SMI_OUTPUT=$(/usr/bin/nvidia-smi -L)
  if [ "$?" -eq 0 ]; then
    GPUS=$(echo "$NVIDIA_SMI_OUTPUT" | /usr/bin/wc -l)
  fi
fi

# write supervisord from template
IPADDRESS_ETH0=$(/usr/sbin/ifconfig $(/usr/sbin/route | awk '/default/{print $NF}') | grep 'inet ' | sed 's/addr://' | awk '{print $2}') 
FQDN=$IPADDRESS_ETH0
sed "s/__IPADDRESS_ETH0__/$IPADDRESS_ETH0/g" $HOME/verdi/etc/supervisord.conf.tmpl | \
  sed "s/__HYSDS_GPU_AVAILABLE__/$GPUS/g" | \
  sed "s/__FQDN__/$FQDN/g" > $HOME/verdi/etc/supervisord.conf

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
if [[ -f $HOME/.aws/credentials ]]; then
  export AWS_ACCESS_KEY_ID="$(grep aws_access_key_id $HOME/.aws/credentials | head -1 | cut -d= -f 2 | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
  export AWS_SECRET_ACCESS_KEY="$(grep aws_secret_access_key $HOME/.aws/credentials | head -1 | cut -d= -f 2 | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
fi

export VERDI_PRIMER_IMAGE="{{ VERDI_PRIMER_IMAGE }}"
export VERDI_PRIMER_IMAGE_BASENAME="$(basename $VERDI_PRIMER_IMAGE 2>/dev/null)"

# Start up Docker Registry if CONTAINER_REGISTRY is defined
export CONTAINER_REGISTRY="{{ CONTAINER_REGISTRY }}"
export CONTAINER_REGISTRY_BUCKET="{{ CONTAINER_REGISTRY_BUCKET }}"
export DOCKER_REGISTRY_IMAGE="s3://{{ CODE_BUCKET }}/docker-registry-2.tar.gz"
export DOCKER_REGISTRY_IMAGE_BASENAME="$(basename $DOCKER_REGISTRY_IMAGE 2>/dev/null)"
if [ ! -z "$CONTAINER_REGISTRY" -a ! -z "$CONTAINER_REGISTRY_BUCKET" ]
then
  rm -rf /tmp/docker-registry-2.tar.gz
  aws s3 cp ${DOCKER_REGISTRY_IMAGE} /tmp/${DOCKER_REGISTRY_IMAGE_BASENAME}
  docker load -i /tmp/${DOCKER_REGISTRY_IMAGE_BASENAME}
  docker run -p 5050:5000 -e REGISTRY_STORAGE=s3 -e REGISTRY_STORAGE_S3_BUCKET={{ CONTAINER_REGISTRY_BUCKET }} -e REGISTRY_STORAGE_S3_REGION={{ AWS_REGION }} --name=registry -d registry:2
fi

rm -rf /tmp/${VERDI_PRIMER_IMAGE_BASENAME}
aws s3 cp ${VERDI_PRIMER_IMAGE} /tmp/${VERDI_PRIMER_IMAGE_BASENAME}
docker load -i /tmp/${VERDI_PRIMER_IMAGE_BASENAME}

docker tag hysds/verdi:{{ VERDI_TAG }} hysds/verdi:latest
