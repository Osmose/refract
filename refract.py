#!/usr/bin/env python
import hashlib
import os
from StringIO import StringIO

import requests
from bs4 import BeautifulSoup
from PIL import Image

from flask import Flask, render_template, redirect, request, url_for


app = Flask(__name__)


ROOT = os.path.dirname(os.path.abspath(__file__))
def path(*parts):
    return os.path.join(ROOT, *parts)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/manifest.webapp')
def manifest():
    app_url = request.args.get('url')

    response = requests.get(app_url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text)

    ctx = {
        'app_url': app_url,
        'name': unicode(soup.find('title').string) or 'Refracted Web App',
        'icons': {
            512: url_for('static', filename='icon_512.png'),
            256: url_for('static', filename='icon_256.png'),
            128: url_for('static', filename='icon_128.png'),
        }
    }

    # Parse meta tags
    icon_to_resize = None
    for tag in soup.findAll('meta'):
        if tag.get('property') == 'og:site_name':
            ctx['name'] = tag['content']
        elif tag.get('property') == 'og:image':
            icon_to_resize = tag['content']

    if icon_to_resize:
        ctx['icons'] = resize(icon_to_resize)

    return (
        render_template('manifest.webapp', **ctx),
        200,
        {'Content-Type': 'application/x-web-app-manifest+json'}
    )


@app.route('/launch')
def launch():
    return redirect(request.args.get('url'))


def resize(url):
    response = requests.get(url)
    response.raise_for_status()

    image = Image.open(StringIO(response.content))
    width, height = image.size

    icons = {}
    filename = hashlib.sha1(url).hexdigest()
    for size in (512,):
        size_filename = '{0}_{1}.png'.format(filename, size)
        image.resize((size, size), Image.BILINEAR).save(path('static', 'app_icons', size_filename))
        icons[size] = url_for('static', filename='app_icons/' + size_filename)

    return icons


if __name__ == "__main__":
    app.run(debug=True)
