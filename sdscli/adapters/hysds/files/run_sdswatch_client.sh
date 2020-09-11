#!/bin/bash
BASE_PATH=$(dirname "${BASH_SOURCE}")
BASE_PATH=$(cd "${BASE_PATH}"; pwd)

source $HOME/verdi/bin/activate

# Start up SDSWatch client
export LOGSTASH_IMAGE="s3://{{ CODE_BUCKET }}/logstash-7.1.1.tar.gz"
export LOGSTASH_IMAGE_BASENAME="$(basename $LOGSTASH_IMAGE 2>/dev/null)"
if [ -z "$(docker images -q logstash:7.1.1)" ]; then
  rm -rf /tmp/logstash-7.1.1.tar.gz
  aws s3 cp ${LOGSTASH_IMAGE} /tmp/${LOGSTASH_IMAGE_BASENAME}
  docker load -i /tmp/${LOGSTASH_IMAGE_BASENAME}
else
  echo "Logstash already exists in Docker. Will not download image"
fi
exec docker run -e HOST=${FQDN} -v /data/work/jobs:/sdswatch/jobs \
  -v $HOME/verdi/log:/sdswatch/log \
  -v sdswatch_data:/usr/share/logstash/data \
  -v $HOME/verdi/etc/sdswatch_client.conf:/usr/share/logstash/config/conf/logstash.conf \
  --name=sdswatch-client logstash:7.1.1 \
  logstash -f /usr/share/logstash/config/conf/logstash.conf --config.reload.automatic
