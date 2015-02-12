;(function($) {
    $('#install-form').on('submit', function(e) {
        e.preventDefault();

        fileInputAsDataURL($('#app-icon')[0], function(iconDataURL) {
            var manifestUrl = location.origin + '/manifest.webapp?' + $.param({
                url: $('#app-url').val(),
                name: $('#app-name').val(),
                icon_data_url: iconDataURL || '',
            });

            var request = window.navigator.mozApps.installPackage(manifestUrl);
            request.onerror = function () {
                console.log('Install failed, error: ' + this.error.name);
                console.log(manifestUrl);
            };
        });
    });

    $('#toggle-extras button').on('click', function() {
        $('#toggle-extras').slideUp(150, function() {
            $('#extras').slideDown(300);
        });
    });

    function fileInputAsDataURL(input, callback) {
        if (input.files && input.files[0]) {
            var reader = new FileReader();
            reader.onload = function(e) {
                callback(e.target.result);
            };
            reader.readAsDataURL(input.files[0]);
        } else {
            callback(null);
        }
    }
})(jQuery);
