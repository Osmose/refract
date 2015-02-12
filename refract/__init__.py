import hashlib
import io
import os
from StringIO import StringIO
from urllib import urlopen
from zipfile import ZipFile

import requests
from bs4 import BeautifulSoup
from PIL import Image

from flask import Flask, render_template, request, url_for


__version__ = '0.1'
app = Flask(__name__)
app.config.from_object('refract.default_settings')
app.config.from_envvar('REFRACT_SETTINGS', silent=True)


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
    icon_url = request.args.get('icon_url');
    webapp = Webapp(url, name=name, icon_url=icon_url)
    return webapp.mini_manifest(), 200, {'Content-Type': 'application/x-web-app-manifest+json'}


@app.route('/webapp.zip')
def webapp_zip():
    url = request.args.get('url')
    name = request.args.get('name')
    icon_url = request.args.get('icon_url')
    webapp = Webapp(url, name=name, icon_url=icon_url)
    return webapp.zipfile(), 200, {'Content-Type': 'application/zip'}


class Webapp(object):
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
            response = requests.get(self.url)
            response.raise_for_status()
            self._soup = BeautifulSoup(response.text)
        return self._soup

    def icon(self):
        if not self._icon:
            self._icon = resize_square(self.fetch_icon(), 512)
        return self._icon

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
        for tag in soup.findAll('meta'):
            if tag.get('property') == 'og:image':
                image = download_image(tag['content'])
                if image:
                    return image

        # Fallback to default icon.
        return Image.open(path('static/icon_512.png'))

    def name(self):
        if not self._name:
            self._name = self.guess_name()
        return self._name

    def guess_name(self):
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

    def mini_manifest(self):
        """
        Generate the mini-manifest for this app that points to the
        zipfile with the full packaged app.
        """
        package_path = url_for('webapp_zip', url=self.url, name=self.name(),
                               icon_url=self.icon_url)
        return render_template('mini_manifest.webapp', name=self.name(), package_path=package_path)

    def manifest(self):
        """Generate the manifest for this app."""
        return render_template('manifest.webapp', name=self.name(), icons={512: 'icon_512.png'})

    def refract_html(self):
        """
        Generate the main HTML file for this app. It just redirects to
        the real app.
        """
        return render_template('refract.html', webapp_url=self.url)

    def zipfile(self):
        """
        Generate a string containing the data for a zipfile containing
        all the files for a packaged app that just redirects to this
        webapp on load.
        """
        out = StringIO()
        with ZipFile(out, 'w') as zipf:
            zipf.writestr('manifest.webapp', self.manifest().encode('utf8'))
            zipf.writestr('refract.html', self.refract_html().encode('utf8'))

            icon_bytes = io.BytesIO()
            self.icon().save(icon_bytes, 'PNG')
            zipf.writestr('icon_512.png', icon_bytes.getvalue())
            icon_bytes.close()

        out.seek(0)
        contents = out.read()
        out.close()
        return contents


def resize_square(image, size):
    width, height = image.size
    if width != size or height != size:
        return image.resize((size, size), Image.BILINEAR)
    else:
        return image


def download_image(image_url):
    response = requests.get(image_url)
    if response.status_code != 200:
        return None

    return Image.open(StringIO(response.content))
