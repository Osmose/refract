import hashlib
import io
import json
import logging
import struct
import os
from logging.handlers import SMTPHandler
from StringIO import StringIO
from textwrap import dedent
from zipfile import ZipFile

import requests
from bs4 import BeautifulSoup
from crxmake import crxmake
from PIL import Image
from requests.exceptions import RequestException

from flask import Flask, render_template, request, url_for


__version__ = '0.1'
app = Flask(__name__)
app.config.from_object('refract.default_settings')
app.config.from_pyfile('settings.py', silent=True)
app.config.from_envvar('REFRACT_SETTINGS', silent=True)


# Log errors to email in production mode.
if not app.debug:
    mail_handler = SMTPHandler('127.0.0.1', app.config['EMAIL_FROM'], app.config['ADMINS'],
                               'Refract Error')
    mail_handler.setLevel(logging.ERROR)
    mail_handler.setFormatter(logging.Formatter(dedent('''
        Message type:       %(levelname)s
        Location:           %(pathname)s:%(lineno)d
        Module:             %(module)s
        Function:           %(funcName)s
        Time:               %(asctime)s

        Message:

        %(message)s
    ''')))
    app.logger.addHandler(mail_handler)


ROOT = os.path.dirname(os.path.abspath(__file__))


def path(*parts):
    return os.path.join(ROOT, *parts)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/manifest.webapp')
def manifest():
    url = request.args.get('url')
    name = request.args.get('name')
    icon_url = request.args.get('icon_url')
    app = OpenWebApp(url, name=name, icon_url=icon_url)
    return app.mini_manifest(), 200, {'Content-Type': 'application/x-web-app-manifest+json'}


@app.route('/webapp.zip')
def open_web_app_zip():
    url = request.args.get('url')
    name = request.args.get('name')
    icon_url = request.args.get('icon_url')
    app = OpenWebApp(url, name=name, icon_url=icon_url)
    return app.zipfile(), 200, {'Content-Type': 'application/x-chrome-extension'}


@app.route('/chrome_app.crx')
def chrome_app_crx():
    url = request.args.get('url')
    name = request.args.get('name')
    icon_url = request.args.get('icon_url')
    app = ChromeApp(url, name=name, icon_url=icon_url)
    return app.crxfile(), 200, {'Content-Type': 'application/c'}


class WebApp(object):
    def __init__(self, url, name=None, icon_url=None):
        self.url = url
        self.id = hashlib.sha1(url).hexdigest()
        self._name = name
        self._icon = None
        self.icon_url = icon_url

        self._soup = None

    def soup(self):
        """
        Fetch the index for the webapp and throw it in BeautifulSoup.
        """
        if not self._soup:
            try:
                response = requests.get(self.url)
                response.raise_for_status()
            except RequestException:
                return None
            self._soup = BeautifulSoup(response.text)
        return self._soup

    def icon(self):
        if not self._icon:
            self._icon = resize_square(self.fetch_icon(), 512)
        return self._icon

    def icon_bytes(self):
        icon_bytes = io.BytesIO()
        self.icon().save(icon_bytes, 'PNG')
        value = icon_bytes.getvalue()
        icon_bytes.close()
        return value

    def fetch_icon(self):
        """
        Generate a PIL image with an appropriate 512x512 icon for this
        app.
        """
        # Use user-supplied icon if possible.
        if self.icon_url:
            image = download_image(self.icon_url)
            if image:
                return image

        # Next preference is Open Graph Images from the app itself.
        soup = self.soup()
        if soup:
            for tag in soup.findAll('meta'):
                if tag.get('property') == 'og:image':
                    image = download_image(tag['content'])
                    if image:
                        return image

        # Fallback to default icon.
        return Image.open(path('static/icon_512.png'))

    def name(self):
        if not self._name:
            self._name = self.fetch_name().strip()
        return self._name

    def fetch_name(self):
        """Fetch an appropriate name for this app."""
        soup = self.soup()

        # Prefer Open Graph Names first.
        for tag in soup.findAll('meta'):
            if tag.get('property') == 'og:site_name':
                return tag['content']

        # Fallback to the title tag.
        title_tag = soup.find('title')
        if title_tag:
            return unicode(title_tag.string)

        # Nothing? Jeez.
        return 'Refracted Web App'


class OpenWebApp(WebApp):
    def mini_manifest(self):
        """
        Generate the mini-manifest for this app that points to the
        zipfile with the full packaged app.
        """
        package_path = url_for('open_web_app_zip', url=self.url, name=self.name(),
                               icon_url=self.icon_url)
        return json.dumps({
            'name': self.name(),
            'description': 'A refracted web app.',
            'package_path': package_path,
            'developer': {
                'name': 'Refract'
            }
        })

    def manifest(self):
        return json.dumps({
            'name': self.name(),
            'description': 'A refracted web app.',
            'launch_path': '/index.html',
            'icons': {
                512: 'icon_512.png'
            },
            'developer': {
                'name': 'Refract'
            }
        })

    def index_html(self):
        return render_template('open_web_app/index.html', app_url=self.url)

    def zipfile(self):
        return build_zipfile({
            'manifest.webapp': self.manifest().encode('utf8'),
            'index.html': self.index_html().encode('utf8'),
            'icon_512.png': self.icon_bytes(),
        })


class ChromeApp(WebApp):
    def manifest(self):
        return json.dumps({
            'manifest_version': 2,
            'name': self.name(),
            'description': 'A refracted web app.',
            'version': '0.1',
            'permissions': ['webview'],
            'app': {
                'background': {
                    'scripts': ['background.js']
                }
            },
            'icons': {
                512: 'icon_512.png'
            }
        })

    def background_js(self):
        return render_template('chrome_app/background.js')

    def index_html(self):
        return render_template('chrome_app/index.html', app_url=self.url)

    def crxfile(self):
        zip_data = build_zipfile({
            'manifest.json': self.manifest().encode('utf8'),
            'background.js': self.background_js().encode('utf8'),
            'index.html': self.index_html().encode('utf8'),
            'icon_512.png': self.icon_bytes(),
        })

        # Adapted from crxmake, which normally only works on files on
        # the filesystem.
        with open(app.config['PRIVATE_KEY']) as f:
            pem = f.read()
        with open(app.config['PUBLIC_KEY']) as f:
            der = f.read()

        sig = crxmake.sign(zip_data, pem)
        der_len = struct.pack("<I", len(der))
        sig_len = struct.pack("<I", len(sig))

        out = StringIO()
        data = [crxmake.MAGIC, crxmake.VERSION, der_len, sig_len, der, sig, zip_data]
        for d in data:
            out.write(d)

        crx = out.getvalue()
        out.close()

        return crx


def resize_square(image, size):
    width, height = image.size
    if width != size or height != size:
        return image.resize((size, size), Image.BILINEAR)
    else:
        return image


def download_image(image_url):
    # Dumb workaround for protocol-relative URLs.
    if image_url.startswith('//'):
        image_url = 'http:' + image_url

    response = requests.get(image_url)
    if response.status_code != 200:
        return None

    return Image.open(StringIO(response.content))


def build_zipfile(files):
    """
    Generate a string containing the data for a zipfile containing the
    given files.

    :param dict files: Dictionary of files to zip. Keys are filenames,
                       values are file contents.
    """
    out = StringIO()
    with ZipFile(out, 'w') as zipf:
        for filename, file_contents in files.items():
            zipf.writestr(filename, file_contents)

    zip_contents = out.getvalue()
    out.close()

    return zip_contents
