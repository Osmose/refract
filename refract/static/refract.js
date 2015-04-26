;(function($) {
    $('#open-web-app-install').on('click', function(e) {
        e.preventDefault();
        installOpenWebApp();
    });

    $('#chrome-app-install').on('click', function(e) {
        e.preventDefault();
        installChromeApp();
    });

    function installChromeApp() {
        var crxUrl = location.origin + '/chrome_app.crx?' + $.param({
            url: $('#app-url').val(),
            name: $('#app-name').val(),
            icon_url: $('#app-icon-url').val(),
        });
        $('#chrome-install-instructions').slideDown(300);
        window.location = crxUrl;
    }

    function installOpenWebApp() {
        var manifestUrl = location.origin + '/manifest.webapp?' + $.param({
            url: $('#app-url').val(),
            name: $('#app-name').val(),
            icon_url: $('#app-icon-url').val(),
        });

        var request = window.navigator.mozApps.installPackage(manifestUrl);
        request.onerror = function () {
            console.log('Install failed, error: ' + this.error.name);
            console.log(manifestUrl);
        };
    }

    $('#toggle-extras button').on('click', function() {
        $('#toggle-extras').slideUp(150, function() {
            $('#extras').slideDown(300);
        });
    });
})(jQuery);
