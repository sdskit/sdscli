broker_url = "amqp://{{ MOZART_RABBIT_USER }}:{{ MOZART_RABBIT_PASSWORD }}@mozart-rabbitmq:5672//"
result_backend = "redis://:{{ MOZART_REDIS_PASSWORD }}@mozart-redis"

task_serializer = "msgpack"
result_serializer = "msgpack"
accept_content = ["msgpack"]

task_acks_late = True
result_expires = 86400
worker_prefetch_multiplier = 1

event_serializer = "msgpack"
worker_send_task_events = True
task_send_sent_event = True
task_track_started = True

task_queue_max_priority = 10

broker_heartbeat = 300
broker_heartbeat_checkrate = 5

imports = [
    "hysds.task_worker",
    "hysds.job_worker",
    "hysds.orchestrator",
]

CELERY_SEND_TASK_ERROR_EMAILS = False
ADMINS = (
    ('Gerald Manipon', 'pymonger@gmail.com'),
)
SERVER_EMAIL = 'ops@mozart-rabbitmq'

HYSDS_HANDLE_SIGNALS = False
HYSDS_JOB_STATUS_EXPIRES = 86400

BACKOFF_MAX_VALUE = 64
BACKOFF_MAX_TRIES = 10

HARD_TIME_LIMIT_GAP = 300

PYMONITOREDRUNNER_CFG = {
    "rabbitmq": {
        "hostname": "mozart-rabbitmq",
        "port": 5672,
        "queue": "stdouterr"
    },

    "StreamObserverFileWriter": {
        "stdout_filepath": "_stdout.txt",
        "stderr_filepath": "_stderr.txt"
    },

    "StreamObserverMessenger": {
        "send_interval": 1
    }
}

MOZART_URL = "https://mozart/mozart/"
MOZART_REST_URL = "https://mozart/mozart/api/v0.1"
JOBS_ES_URL = "http://mozart-elasticsearch:9200"
JOBS_PROCESSED_QUEUE = "jobs_processed"
USER_RULES_JOB_QUEUE = "user_rules_job"
ON_DEMAND_JOB_QUEUE = "on_demand_job"
USER_RULES_JOB_INDEX = "user_rules-mozart"
STATUS_ALIAS = "job_status"

TOSCA_URL = "https://{{ GRQ_PVT_IP }}/search/"
GRQ_URL = "http://{{ GRQ_PVT_IP }}:{{ GRQ_PORT }}"
GRQ_REST_URL = "http://{{ GRQ_PVT_IP }}:{{ GRQ_PORT }}/api/v0.1"
GRQ_UPDATE_URL = "http://{{ GRQ_PVT_IP }}:{{ GRQ_PORT }}/api/v0.1/grq/dataset/index"
GRQ_ES_URL = "http://{{ GRQ_ES_PVT_IP }}:9200"
DATASET_PROCESSED_QUEUE = "dataset_processed"
USER_RULES_DATASET_QUEUE = "user_rules_dataset"
ON_DEMAND_DATASET_QUEUE = "on_demand_dataset"
USER_RULES_DATASET_INDEX = "user_rules-grq"
DATASET_ALIAS = "grq"

USER_RULES_TRIGGER_QUEUE = "user_rules_trigger"

REDIS_JOB_STATUS_URL = "redis://:{{ MOZART_REDIS_PASSWORD }}@mozart-redis"
REDIS_JOB_STATUS_KEY = "logstash"
REDIS_JOB_INFO_URL = "redis://:{{ METRICS_REDIS_PASSWORD }}@{{ METRICS_REDIS_PVT_IP }}"
REDIS_JOB_INFO_KEY = "logstash"
REDIS_INSTANCE_METRICS_URL = "redis://:{{ METRICS_REDIS_PASSWORD }}@{{ METRICS_REDIS_PVT_IP }}"
REDIS_INSTANCE_METRICS_KEY = "logstash"
REDIS_UNIX_DOMAIN_SOCKET = "unix://:{{ MOZART_REDIS_PASSWORD }}@/data/redis/redis.sock"

WORKER_CONTIGUOUS_FAILURE_THRESHOLD = 10
WORKER_CONTIGUOUS_FAILURE_TIME = 5.

ROOT_WORK_DIR = "/data/work"
WEBDAV_URL = None
WEBDAV_PORT = 8085

WORKER_MOUNT_BLACKLIST = [
    "/dev",
    "/etc",
    "/lib",
    "/proc",
    "/usr",
    "/var",
]
