import subprocess
import shlex
from app import celery, settings, db
from models import Account
import redis
from datetime import datetime, timedelta
from reset_tor import reset as reset_tor


@celery.task
def run_command(command, info):
    reset_tor(9051)
    j = Job(run_command.request.id, info)
    result = j.run(command)
    j.finish(result)


class Job:
    def __init__(self, id, info):
        self.id = "job_%s" % id
        self.state = None
        self.redis = redis.StrictRedis(host=settings.REDIS_URL,
                        port=settings.REDIS_PORT, db=settings.REDIS_DB)
        self.info = info

        for key, value in info.iteritems():
            self.redis.hset(self.id, key, value)

        self.redis.hset(self.id, 'start_time', str(datetime.utcnow()))

    def log(self, message):
        self.redis.append(self.id + "_l", message)

    def _manage_history(self, list, id):
        length = self.redis.llen(list)
        if length + 1 >= settings.HISTORY_LENGTH:
            self.redis.rpop(list)

        self.redis.lpush(list, id)

    def set_state(self, code):
        self.redis.hset(self.id, 'state', code)

        if code == 9:  # running
            self.redis.lpush('running', self.id)
            return

        if code == 0:
            self._manage_history('successful', self.id)

        else:
            self._manage_history('failed', self.id)

        self.redis.lrem('running', 0, self.id)
        self.redis.hset(self.id, 'end_time', str(datetime.utcnow()))

    def run(self, command):
        self.set_state(9)
        self.log("Starting... %s\n" % self.id)
        self.log("Command %s\n" % command)

        store = []
        last_send_time = datetime.now()

        command = shlex.split(command)
        proc = subprocess.Popen(command, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        while proc.poll() is None:
            output = proc.stdout.readline()
            store.append(output)
            print output
            print store
            if datetime.now() > timedelta(seconds=settings.REDIS_FLUSH_TIME) + last_send_time:
                if len(store) > 0:
                    print "SAVING"
                    self.log("".join(store))

                store = []
                last_send_time = datetime.now()

        self.log("".join(store))
        result_code = proc.poll()
        return result_code

    def finish(self, result_code):
        self.set_state(result_code)
        account = Account.query.get(self.info['account_id'])
        account.last_action = datetime.utcnow()
        account.active = False

        if result_code == 0:
            self.log("Finished successfully!")
            account.fail_count = 0
        else:
            self.log("Failed!")
            account.fail_count += 1

        db.session.add(account)
        db.session.commit()
