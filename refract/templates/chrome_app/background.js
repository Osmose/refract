chrome.app.runtime.onLaunched.addListener(function() {
    chrome.app.window.create('index.html', {
        'bounds': {
          'width': {{ width|default(800) }},
          'height': {{ height|default(600) }}
        }
    });
});
