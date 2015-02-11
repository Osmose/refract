# Refract

Refract is a small web service that takes a URL and generates an [Open Web App](https://developer.mozilla.org/en-US/Apps) that redirects immediately to the given URL. In other words, this lets you install websites as applications, similar to the now-defunct [Prism add-on](http://en.wikipedia.org/wiki/Mozilla_Prism).

After I found myself manually creating apps for some of my favorite websites, I figured it was worth automating and sharing.

## Developer Setup

1. Set up a [virtualenv](https://virtualenv.pypa.io/en/latest/). I highly recommend [virtualenvwrapper](http://virtualenvwrapper.readthedocs.org/en/latest/).

2. Install requirements:

   ```sh
   $ pip install -r requirements.txt
   ```

3. Run the development server:

   ```sh
   $ ./manage.py run
   ```

## Thanks

Thanks to Martha Ormiston from the Noun Project for the default prism icon.

## License

This project is licensed under the MIT license. See the `LICENSE` file for details.
