from __future__ import with_statement
from fabric.api import *

## Currently, these helpers return commands
## We may want to eventually return execution booleans in the future

# Use tee to append a line to a file
def append(filename, line):
  cmd = "echo '%s' | tee -a %s" % (line, filename)
  return cmd

# Check to see if a package is installed
def is_installed(package):
  cmd = 'dpkg-query -l "%s" | grep -q ^.i'
  cmd = cmd % (package)
  return cmd

# Install a package without prompts
def install(package):
  cmd = 'apt-get --force-yes --yes install %s' % (' '.join(package))
  return cmd

# Update apt
def update():
  cmd = 'apt-get update'
  return cmd

# Use if you need to run a command as another user
def run_su(command, user):
  cmd = ('su %s -c "%s"' % (user, command) )
  return cmd

# Output Start
def start(app):
  return "Installing %s..." % (app)

# Output Finish
def success(app):
  return "Successfully installed %s" % (app)

# Output Failures
def failed(app):
  return "Failed to install %s" % (app)