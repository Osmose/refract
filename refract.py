#!/usr/bin/env python
import hashlib
import json
import os
import shutil
from StringIO import StringIO
from zipfile import ZipFile

import requests
from bs4 import BeautifulSoup
from PIL import Image

from flask import Flask, render_template, redirect, request, send_from_directory, url_for


__version__ = '0.1'
app = Flask(__name__)


ROOT = os.path.dirname(os.path.abspath(__file__))
def path(*parts):
    return os.path.join(ROOT, *parts)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/launch')
def launch():
    return redirect(request.args.get('url'))


@app.route('/manifest.webapp')
def manifest():
    url = request.args.get('url')
    webapp = generate_packaged_app(url)

    if app.debug:
        return send_from_directory(webapp.path(), 'manifest.webapp',
                                   mimetype='application/x-web-app-manifest+json')
    else:
        return redirect(webapp.static_path('manifest.webapp'))


class Webapp(object):
    def __init__(self, url):
        self.url = url
        self.id = hashlib.sha1(url).hexdigest()
        self.file_path = path('static', 'apps', self.id)
        self.static_path_prefix = '/'.join(['apps', self.id])

    def path(self, *parts):
        return os.path.join(self.file_path, *parts)

    def content_path(self, *parts):
        return self.path('content', *parts)

    def static_path(self, *parts):
        parts = [self.static_path_prefix] + list(parts)
        return url_for('static', filename='/'.join(parts))


def generate_packaged_app(url):
    webapp = Webapp(url)

    # Clear out old app stuff (someday we'll be more efficient maybe).
    if os.path.exists(webapp.path()):
        shutil.rmtree(webapp.path())
    os.makedirs(webapp.content_path())

    generate_manifest(url, webapp)
    generate_zip(webapp)
    generate_mini_manifest(webapp)

    return webapp


def generate_manifest(url, webapp):
    response = requests.get(webapp.url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text)

    ctx = {
        'webapp_url': webapp.url,
        'name': unicode(soup.find('title').string) or 'Refracted Web App',
    }

    # Parse meta tags
    icon_to_resize = None
    for tag in soup.findAll('meta'):
        if tag.get('property') == 'og:site_name':
            ctx['name'] = tag['content']
        elif tag.get('property') == 'og:image':
            icon_to_resize = tag['content']

    if icon_to_resize:
        ctx['icons'] = resize_and_save(icon_to_resize, webapp)
    else:
        shutil.copy(path('static', 'icon_512.png'), webapp.content_path('icon_512.png'))
        ctx['icons'] = {512: 'icon_512.png'}

    with open(webapp.content_path('refract.html'), 'w') as f:
        f.write(render_template('refract.html', **ctx))

    with open(webapp.content_path('manifest.webapp'), 'w') as f:
        f.write(render_template('manifest.webapp', **ctx))


def generate_zip(webapp):
    with ZipFile(webapp.path('webapp.zip'), 'w') as zipf:
        zipf.write(webapp.content_path('manifest.webapp'), 'manifest.webapp')
        zipf.write(webapp.content_path('refract.html'), 'refract.html')
        zipf.write(webapp.content_path('icon_512.png'), 'icon_512.png')


def generate_mini_manifest(webapp):
    with open(webapp.content_path('manifest.webapp'), 'r') as f:
        manifest = json.loads(f.read())

    del manifest['launch_path']
    manifest['package_path'] = webapp.static_path('webapp.zip')
    manifest['size'] = os.stat(webapp.path('webapp.zip')).st_size
    for size, url in manifest['icons'].items():
        manifest['icons'][size] = 'content/' + url

    with open(webapp.path('manifest.webapp'), 'w') as f:
        f.write(json.dumps(manifest))


# TODO: Could use a better name, needs some refactoring.
def resize_and_save(url, webapp):
    response = requests.get(url)
    response.raise_for_status()

    image = Image.open(StringIO(response.content))
    width, height = image.size

    image.resize((512, 512), Image.BILINEAR).save(webapp.content_path('icon_512.png'))
    return {512: 'icon_512.png'}


if __name__ == "__main__":
    app.run(debug=True)
