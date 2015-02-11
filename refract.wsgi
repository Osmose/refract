import os
import pwd
import sys


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def path(*paths):
    return os.path.join(BASE_DIR, *paths)


os.environ['REFRACT_CONFIG'] = path('settings.py')
# http://code.google.com/p/modwsgi/wiki/ApplicationIssues#User_HOME_Environment_Variable
os.environ['HOME'] = pwd.getpwuid(os.getuid()).pw_dir

activate_this = path('venv/bin/activate_this.py')
execfile(activate_this, dict(__file__=activate_this))


BASE_DIR = os.path.join(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from refract import app as application
