var oscar = oscar || {};
oscar.checkout = {
    gateway: {
        init: function() {
            var radioWidgets = $('form input[name=options]');
            oscar.checkout.gateway.handleRadioSelection(radioWidgets.val());
            radioWidgets.change(oscar.checkout.gateway.handleRadioChange);
        },
        handleRadioChange: function() {
            oscar.checkout.gateway.handleRadioSelection($(this).val());
        },
        handleRadioSelection: function(value) {
            var pwInput = $('#id_password');
            if (value == 'new') {
                pwInput.attr('disabled', 'disabled');
            } else {
                pwInput.removeAttr('disabled');
            }
        }
    }
};
