var oscar = oscar || {};
oscar.basket = {
    is_form_being_submitted: false,
    init: function() {
        $('#basket_formset a[data-behaviours~="remove"]').click(function() {
            oscar.basket.checkAndSubmit($(this), 'form', 'DELETE');
        });
        $('#basket_formset a[data-behaviours~="save"]').click(function() {
            oscar.basket.checkAndSubmit($(this), 'form', 'save_for_later');
        });
        $('#basket_formset').submit(oscar.basket.submitForm);
        $('#saved_basket_formset a[data-behaviours~="move"]').click(function() {
            oscar.basket.checkAndSubmit($(this), 'saved', 'move_to_basket');
            e.preventDefault();
        });
        $('#saved_basket_formset a[data-behaviours~="remove"]').click(function() {
            oscar.basket.checkAndSubmit($(this), 'saved', 'DELETE');
            e.preventDefault();
        });
        $('#voucher_form_link a').click(function(e) {
            oscar.basket.showVoucherForm();
            e.preventDefault();
        });
        $('#voucher_form_cancel').click(function(e) {
            oscar.basket.hideVoucherForm();
            e.preventDefault();
        });
        if (window.location.hash == '#voucher') {
            oscar.basket.showVoucherForm();
        }
    },
    submitForm: function(e) {
        $('#messages').html('');
        var payload = $('#basket_formset').serializeArray();
        $.post('/basket/', payload, oscar.basket.submitFormSuccess, 'json');
        e.preventDefault();
    },
    submitFormSuccess: function(data) {
        $('#content_inner').html(data.content_html);
        $('#messages').html('');
        for (var level in data.messages) {
            for (var i=0; i<data.messages[level].length; i++) {
                oscar.messages[level](data.messages[level][i]);
            }
        }
        oscar.basket.init();
    },
    showVoucherForm: function() {
        $('#voucher_form_container').show();
        $('#voucher_form_link').hide();
    },
    hideVoucherForm: function() {
        $('#voucher_form_container').hide();
        $('#voucher_form_link').show();
    },
    checkAndSubmit: function($ele, formPrefix, idSuffix) {
        if (oscar.basket.is_form_being_submitted) {
            return;
        }
        var formID = $ele.attr('data-id');
        var inputID = '#id_' + formPrefix + '-' + formID + '-' + idSuffix;
        $(inputID).attr('checked', 'checked');
        $ele.closest('form').submit();
        oscar.basket.is_form_being_submitted = true;
    }
};
oscar.checkout = {
    init: function() {
    },
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
