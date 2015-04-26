#!/usr/bin/env python
from flask.ext.script import Manager

from refract import app


manager = Manager(app)


@manager.command
def runserver():
    app.run(debug=True, port=8000)


if __name__ == "__main__":
    manager.run()
