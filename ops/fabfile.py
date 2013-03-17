from fabric.api import run, sudo, cd, env, settings, put
from fabric.colors import red, green
from fabric.utils import abort, puts
from fabric.contrib.files import append
from fabric.contrib.project import rsync_project as rsync
import boto.ec2
import time
from app import settings as app_settings

env.user = 'ubuntu'
env.key_filename = './ops/private/hermes.pem'
env.connection_attempts = 3
env.timeout = 15
conn = None


def _get_conn():
    global conn
    if conn is None:
        t_conn = boto.ec2.connect_to_region('us-east-1',
            aws_access_key_id=app_settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=app_settings.AWS_SECRET_ACCESS_KEY)

        if t_conn is None:
            puts(red("Failed to connect to EC2"))
            abort("Fatal Error")

        conn = t_conn
    return conn


def _launch_instance(type='t1.micro'):
    puts("Creating instance...")
    ec2 = _get_conn()
    reservation = ec2.run_instances('ami-3fec7956',
            key_name='hermes',
            security_groups=['hermes'],
            instance_type=type)

    instance = reservation.instances[0]

    while True:
        time.sleep(5)
        instance.update()
        puts("%s (%s)" % (instance.state, instance.state_code))
        if instance.state_code != 0:
            break

    puts("Instance created " + instance.public_dns_name)
    return instance.public_dns_name, instance.id


def _terminate_instance(ids):
    puts("Killing " + ids)
    if type(ids) == str:
        ids = ids.split(',')

    ec2 = _get_conn()
    ec2.terminate_instances(ids)


def install_master_deps():
    sudo("apt-get install -y htop redis-server")


def install_python_deps():
    sudo("apt-get install -y python python-pip libevent-dev make postgresql postgresql-server-dev-9.1 postgresql-client pep8 python-dev python-setuptools build-essential")
    with cd(app_settings.PATH):
        sudo("pip install --upgrade -r requirements.txt")


def install_node():
    sudo("apt-get install -y python-software-properties python g++ make")
    sudo("FORCE_ADD_APT_REPOSITORY=1 add-apt-repository ppa:chris-lea/node.js")
    sudo("apt-get update")
    sudo("apt-get install -y nodejs")


def install_captcha_deps():
    with cd(app_settings.PATH + "/captcha-buster"):
        run("npm install")


def install_phantomjs():
    sudo("apt-get install -y libfontconfig")
    run("wget http://phantomjs.googlecode.com/files/phantomjs-1.8.1-linux-x86_64.tar.bz2")
    run("tar xvjf phantomjs*")
    with cd("phantomjs*"):
        run("chmod a+rwx ./bin/phantomjs")
        sudo("ln -s `pwd`/bin/phantomjs /usr/bin/phantomjs")

    run('phantomjs --version')


def install_casperjs():
    run("wget https://github.com/n1k0/casperjs/tarball/1.0.2")
    run("tar zxvf 1.0.2")
    with cd("n1k0*"):
        run('ls')
        run("chmod a+rwx ./bin/casperjs")
        sudo("ln -s `pwd`/bin/casperjs /usr/bin/casperjs")

    run('casperjs --version')


def install_tor():
    append('/etc/apt/sources.list',
            'deb     http://deb.torproject.org/torproject.org precise main',
            use_sudo=True)

    sudo("gpg --keyserver keys.gnupg.net --recv 886DDD89")
    sudo("gpg --export A3C4F0F979CAA22CDBA8F512EE8CBC9E886DDD89 | sudo apt-key add -")
    sudo("apt-get update")
    sudo("apt-get install -y deb.torproject.org-keyring")
    sudo("apt-get install -y tor")


def full_update():
    sudo("apt-get update")
    sudo("apt-get upgrade -y")


def sync():
    sudo("mkdir -p /srv")
    sudo("chmod a+w /srv")
    rsync("/srv", exclude=['.git', 'build', '*node_modules*', '*.swp', '*.pyc'])


def first_fetch():
    sudo("apt-get update")
    sudo("apt-get install -y git")
    sudo("mkdir -p " + app_settings.PATH)
    sudo("chmod -R a+w " + app_settings.PATH)
    with cd(app_settings.PATH):
        run("git clone https://github.com/nickhs/hermes.git .")


def fetch():
    with cd(app_settings.PATH):
        run("git pull")


def worker_supervisor():
    _setup_supervisor()
    put('ops/private/worker_supervisord.conf', '/etc/supervisor/conf.d/worker_supervisord.conf', use_sudo=True)
    sudo('supervisorctl reload')


def master_supervisor():
    _setup_supervisor()
    put('ops/private/master_supervisord.conf', '/etc/supervisor/conf.d/master_supervisord.conf', use_sudo=True)
    sudo('supervisorctl reload')


def captcha_supervisor():
    _setup_supervisor()
    put('ops/private/captcha_supervisord.conf', '/etc/supervisor/conf.d/captcha_supervisord.conf', use_sudo=True)
    sudo('supervisorctl reload')


def _setup_supervisor():
    sudo('mkdir -p /var/log/hermes')
    sudo('chmod a+rw /var/log/hermes')
    sudo('apt-get install -y supervisor')


def copy_override():
    put('prod_settings_override.py', app_settings.PATH + '/settings_override.py')


def conf_sync_master():
    put('ops/private/pg_hba.conf', '/etc/postgresql/9.1/main/pg_hba.conf', use_sudo=True)
    put('ops/private/postgresql.conf', '/etc/postgresql/9.1/main/postgresql.conf', use_sudo=True)
    sudo('service postgresql restart')

    put('ops/private/create_db.sql', '/tmp/create_db.sql')
    sudo('sudo -u postgres psql -a -f /tmp/create_db.sql')
    put('ops/private/redis.conf', '/etc/redis/redis.conf', use_sudo=True)
    sudo('service redis-server restart')


def shell():
    run('ssh -i %s -l %s %s' % (app_settings.PATH + env.key_filename.lstrip('.'), env.user, env.hosts[0]))


def launch_base():
    host, id = _launch_instance()
    with settings(host_string=host):
        full_update()
        first_fetch()
        copy_override()

    return host, id


def launch_worker(launch=True, host=None):
    host, id = launch_base()
    with settings(host_string=host):
        install_tor()
        install_python_deps()
        install_phantomjs()
        install_casperjs()
        worker_supervisor()
        puts(green("All done! " + host))


def launch_master():
    host, id = launch_base()
    with settings(host_string=host):
        install_python_deps()
        install_master_deps()
        conf_sync_master()
        with cd(app_settings.PATH):
            run('python bootstrap.py')

        master_supervisor()
        puts(green("All done! " + host))
