#!/usr/bin/env python
from flask import Flask, render_template, request, url_for


app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/manifest.webapp')
def manifest():
    app_url = request.args.get('url')
    icon_512_url = request.args.get('icon_512', url_for('static', filename='icon_512.png'))
    icon_256_url = request.args.get('icon_256', url_for('static', filename='icon_256.png'))
    icon_128_url = request.args.get('icon_128', url_for('static', filename='icon_128.png'))
    return render_template(
        'manifest.webapp',
        app_url=app_url,
        icon_512_url=icon_512_url,
        icon_256_url=icon_256_url,
        icon_128_url=icon_128_url
    ), 200, {'Content-Type': 'application/x-web-app-manifest+json'}


@app.route('/app.html')
def app_page():
    app_url = request.args.get('url')
    return render_template('app.html', app_url=app_url)


@app.route('/install.html')
def install():
    app_url = request.args.get('url')
    manifest_url = url_for('manifest', _external=True, url=app_url)
    return render_template('install.html', manifest_url=manifest_url)


if __name__ == "__main__":
    app.run(debug=True)
