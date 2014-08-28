# -*- coding: utf-8 -*-
#!/usr/bin/python

from __future__ import with_statement
import os, re, ConfigParser 
from getpass import getpass
from fabric.api import *
from fabric.state import env
from fabric.contrib.files import exists, upload_template
from fabric.operations import prompt
from helper import *

config = ConfigParser.ConfigParser()
config.read('config.conf')
conf = {}
for s in config.sections():
  section = {}
  for k,v in config.items(s):
    section[k] = v
  conf[s] = section

conf['user_name'] = prompt("Enter your UNIX user name: ")
conf['ip'] = prompt("Enter your target IP address: ")

env.hosts = ['%s@%s' % (conf['user_name'], conf['ip'])]
env.roledefs = {
  'dev': ['%s@%s' % (conf['user_name'], conf['ip'])],
  'db': ['oracle@%s' % (conf['ip'])]
}

def home():
  app = "Home Directory Test"
  with lcd('$HOME'):
    c = run('ls')
    print (success(app) if c.succeeded else failed(app))
  execute(test)

@roles('db')
def test():
  run('sqlplus / as sysdba')

def apt_proxy():
  print "Adding apt proxy entries"
  for k in conf['apt-proxy']:
    sudo(append('/etc/apt/apt.conf', conf['apt-proxy'][k]))

def bash_proxy():
  print "Adding bash proxy entries"
  run(append('~/.bashrc', '\n#### PROXY ####'))
  for k in conf['bash-proxy']:
    run(append('~/.bashrc', conf['bash-proxy'][k]))
  run('source ~/.bashrc')

def environment_proxy():
  print "Adding environment proxy entries"
  sudo(append('/etc/environment', '\n#### PROXY ####'))
  for k in conf['bash-proxy']:
    sudo(append('/etc/environment', conf['bash-proxy'][k]))

def bash_oracle():
  print "Adding bash oracle entries"
  run(append('~/.bashrc', '\n#### ORACLE ####'))
  for k in conf['oracle']['exports'].split(","):
    run(append('~/.bashrc', 'export %s' % (k) ))
  run('source ~/.bashrc')

def copy_packages():
  print "Transferring packages to client..."
  with settings(warn_only=True):
    sudo('mkdir %s' % (conf['global']['package_dir']))
  c = put('packages/*', conf['global']['package_dir'], use_sudo=True)
  print ("Successfully copied packages." if c.succeeded else "Failed copying packages.")

def remove_packages():
  print "Removing packages..."
  c = sudo('rm -rf %s' % (conf['global']['package_dir']))
  print ("Successfully removed packages." if c.succeeded else "Failed removing packages.")

def install_chrome():
  app = "Google Chrome"
  print start(app)
  sudo('apt-get install libxss1')
  c = sudo('dpkg -i %s/google-chrome*.deb' % (conf['global']['package_dir']) )
  print (success(app) if c.succeeded else failed(app))

def install_guest_additions():
  app = "VBoxGuestAdditions_4.3.8"
  print start(app)
  with settings(warn_only=True):
    mount_dir='/media/vbox'
    dependencies = [
      'dkms',
      'linux-headers-$(uname -r)',
      'build-essential'
    ]
    sudo(install(dependencies))
    sudo('mkdir %s' % (mount_dir))
    sudo('mount -t iso9660 -o loop "%s/VBoxGuestAdditions_4.3.8.iso" %s' % (conf['global']['package_dir'], mount_dir))
    c = sudo('sh %s/VBoxLinuxAdditions.run' % mount_dir)
    print (success(app) if c.succeeded else failed(app))
    sudo('umount %s' % (mount_dir))
    sudo('rmdir %s' % (mount_dir))

def install_dev_packages():
  app = "miscellaneous developer packages"
  print start(app)
  c = sudo(install([
    'build-essential',
    'vim',
    'curl',
    'git',
    'gitk',
    'fabric']))
  print (success(app) if c.succeeded else failed(app))

def install_oracle():
  app = "oracle-xe-11"
  print start(app)
  dependencies = [
    'openjdk-7-jdk',
    'openjdk-7-jre',
    'alien',
    'libaio1',
    'libc6',  
    'unixodbc']
  sudo(install(dependencies))
  
  # General Oracle configs
  put('templates/chkconfig', '/sbin', use_sudo=True)
  sudo('chmod 755 /sbin/chkconfig')
  put('templates/60-oracle.conf', '/etc/sysctl.d', use_sudo=True)
  
  # Configuration for memory allocation
  put('templates/S01shm_load', '/etc/rc2.d', use_sudo=True)
  sudo('chmod 755 /etc/rc2.d/S01shm_load')
  reboot(wait=100)
  copy_packages()

  with settings(warn_only=True):
    sudo('groupadd dba')
    sudo('usermod -a -G dba %s' % (conf['user_name']) )
    sudo('ln -s /usr/bin/awk /bin/awk')
    run('mkdir /var/lock/subsys')
    run('touch /var/lock/subsys/listener')
  c = sudo('alien --scripts -i -d %s/oracle-xe-11.2.0-1.0.x86_64.rpm' % (conf['global']['package_dir']) )
  # sudo('cp %s/bin/oracle %s/bin/oracle.bak' % (conf['oracle']['oracle_dir'],conf['oracle']['oracle_dir']) )
  # sudo('sed "s|/dev/shm|/run/shm|g" %s/bin/oracle.bak >%s/bin/oracle' % (conf['oracle']['oracle_dir'],conf['oracle']['oracle_dir']) )
  sudo('chmod -R g+rwx /u01/app/oracle')
  sudo('chown -R oracle:dba /u01/app/oracle')
  
  with settings(warn_only=True):
    sudo('usermod -a -G dba oracle')
  d = sudo('echo -e "8080\n1521\n%s\n%s\ny\n" | /etc/init.d/oracle-xe configure' % (conf['db_password'],conf['db_password']))

  sudo('echo -e "%s\n%s" | passwd oracle' % (conf['db_password'], conf['db_password']))

  print (success(app) if c.succeeded and d.succeeded else failed(app))

def upload_db_scripts():
  upload_template(
    filename='tnsnames.ora',
    destination='%s/network/admin' % (conf['oracle']['oracle_dir']),
    context=conf,
    use_jinja=True,
    template_dir='templates',
    use_sudo=True
  )
  upload_template(
    filename='user.sql',
    destination=conf['global']['package_dir'],
    context=conf,
    use_jinja=True,
    template_dir='templates',
    use_sudo=True
  )

@roles('db')
def create_db_users():
  bash_oracle()
  run('sqlplus / as SYSDBA < %s/user.sql' % (conf['global']['package_dir']) )

def install_ruby():
  app = "Ruby 1.9.3-p362"
  dependencies = [
    'gawk',
    'libreadline6-dev',
    'zlib1g-dev',
    'qt4-qmake',
    'libxml2',
    'libxml2-dev',
    'libssl-dev',
    'libyaml-dev',
    'libsqlite3-dev',
    'libqt4-dev',
    'sqlite3',
    'autoconf',
    'libgdbm-dev',
    'libncurses5-dev',
    'automake',
    'libtool',
    'bison',
    'libffi-dev',
    'unixodbc-dev'
  ]
  print start(app)
  c = run('\curl -L https://get.rvm.io | bash -s stable')
  run('source ~/.rvm/scripts/rvm')
  sudo(update())
  sudo(install(dependencies))
  run('rvm install 1.9.3-p362')
  run('rvm use 1.9.3-p362 --default')
  print (success(app) if c.succeeded else failed(app))

def install_sqldeveloper():
  app = "sqldeveloper-4.0.2.15.21-1"
  print start(app)
  dependencies = ['alien']
  sudo(install(dependencies))
  c = sudo('alien --scripts -i -d %s/sqldeveloper-4.0.2.15.21-1.noarch.rpm' % (conf['global']['package_dir']) )
  print (success(app) if c.succeeded else failed(app))

def install_python():
  app = "python dev"
  dependencies = [
  'python',
  'python-pip',
  'fabric',
  ]
  sudo(install(dependencies))
  sudo('pip install virtualenv')

def set_git_config():
  upload_template(
    filename='.gitconfig',
    destination='~/',
    context=conf,
    use_jinja=True,
    template_dir='templates',
    use_sudo=True
  )

def clone_repos():
  with settings(warn_only=True):
    run('mkdir ~/dev')
    with cd('~/dev'):
      for r in conf['repos']:
        print "Cloning %s" % (r)
        run('git clone %s' % (conf['repos'][r]) )

def copy_configs():
  put('packages/certs.tar.gz', '~/')
  # run('tar -xvzf ~/dev/rsam/certs/certs.tar.gz ~/dev/rsam/certs/')
  # run('tar -xvzf ~/dev/self_service/certs/certs.tar.gz ~/dev/self_service/certs/')
  with settings(warn_only=True):
    upload_template(
      filename='database.yml',
      destination='~/dev/rsam/config',
      context=conf,
      use_jinja=True,
      template_dir='templates',
      use_sudo=True
    )

    upload_template(
      filename='database.yml',
      destination='~/dev/self_service/config',
      context=conf,
      use_jinja=True,
      template_dir='templates',
      use_sudo=True
    )

def deploy():
  # Grab some data from user to build files
  conf['email'] = prompt("Enter your JPMChase email address:")
  conf['first_name'] = prompt("Enter your first name: ").lower()
  conf['last_name'] = prompt("Enter your last name: ").lower()
  conf['sid'] = prompt("Enter your JPMChase SID:")
  conf['db_password'] = getpass("Please enter a new password for your local test database: ")
  
  # Build some configuration
  conf['db_name'] = '%s_local' % conf['first_name']

  # Let er rip!
  apt_proxy()
  bash_proxy()
  environment_proxy()
  reboot(wait=100)
  copy_packages()
  install_guest_additions()
  install_dev_packages()
  install_chrome()
  install_ruby()
  bash_oracle()
  install_oracle()
  upload_db_scripts()
  execute(create_db_users)
  install_sqldeveloper()
  set_git_config()
  clone_repos()
  copy_configs()
  remove_packages()
  install_python()