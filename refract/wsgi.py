import os
import sys


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def path(*paths):
    return os.path.join(BASE_DIR, *paths)


os.environ['REFRACT_SETTINGS'] = path('settings.py')
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)


from refract import app as application  # NOQA
