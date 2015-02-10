;(function($) {
    $('#install-form').on('submit', function(e) {
        e.preventDefault();

        var url = $('#app-url').val();
        var manifestUrl = location.origin + '/manifest.webapp?url=' + encodeURIComponent(url);
        var request = window.navigator.mozApps.install(manifestUrl);
        request.onerror = function () {
            console.log('Install failed, error: ' + this.error.name);
            console.log(manifestUrl);
        };
    });
})(jQuery);
