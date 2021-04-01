from psycogreen.gevent import patch_psycopg

capture_output = True


def post_fork(server, worker):
    patch_psycopg()
    worker.log.info("Enabled async Psycopg2")
