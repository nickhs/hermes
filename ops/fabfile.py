from fabric.api import run, sudo, cd, env
from fabric.colors import red
from fabric.utils import abort, puts
from fabric.contrib.files import append
from fabric.contrib.project import rsync_project as rsync
import boto.ec2
import time
from app import settings

env.user = 'ubuntu'
env.key_filename = './ops/private/hermes.pem'
conn = None


def _get_conn():
    global conn
    if conn is None:
        t_conn = boto.ec2.connect_to_region('us-east-1',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)

        if t_conn is None:
            print(red("Failed to connect to EC2"))
            abort("Fatal Error")

        conn = t_conn
    return conn


def launch_instance():
    puts("Creating instance...")
    ec2 = _get_conn()
    reservation = ec2.run_instances('ami-3fec7956',
            key_name='hermes',
            security_groups=['hermes'],
            instance_type='t1.micro')

    instance = reservation.instances[0]

    while True:
        time.sleep(5)
        instance.update()
        puts("%s (%s)" % (instance.state, instance.state_code))
        if instance.state_code != 0:
            break

    puts("Instance created " + instance.public_dns_name)
    return instance.public_dns_name


def install_python_deps():
    sudo("pip install --upgrade -r requirements.txt")


def install_node():
    sudo("apt-get install -y python-software-properties python g++ make")
    sudo("FORCE_ADD_APT_REPOSITORY=1 add-apt-repository ppa:chris-lea/node.js")
    sudo("apt-get update")
    sudo("apt-get install -y nodejs npm")


def install_captcha_deps():
    with cd(settings.PATH + "/captcha-buster"):
        run("npm install")


def install_phantomjs():
    sudo("apt-get install -y libfontconfig")
    run("wget http://phantomjs.googlecode.com/files/phantomjs-1.8.1-linux-x86_64.tar.bz2")
    run("tar xvjf phantomjs*")
    with cd("phantomjs*"):
        run("chmod a+rwx ./bin/phantomjs")
        sudo("ln -s `pwd`/bin/phantomjs /usr/bin/phantomjs")


def install_casperjs():
    run("wget https://github.com/n1k0/casperjs/tarball/1.0.2")
    run("tar zxvf 1.0.2")
    with cd("n1k0*"):
        run('ls')
        run("chmod a+rwx ./bin/casperjs")
        sudo("ln -s `pwd`/bin/casperjs /usr/bin/casperjs")


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
    run("mkdir -p /srv")
    sudo("chmod a+w /srv")
    rsync("/srv", exclude=['.git', 'build', '*node_modules*', '*.swp', '*.pyc'])


def first_fetch():
    sudo("apt-get install -y git-core")
    run("mkdir -p /srv/hermes")
    sudo("chmod -R a+w /srv/hermes")
    with cd("/srv/hermes"):
        run("git clone https://github.com/nickhs/hermes.git")


def fetch():
    with cd("/srv/hermes"):
        run("git pull")


def launch_worker():
    host = launch_instance()
    env.hosts = [host]
    full_update()
    first_fetch()
