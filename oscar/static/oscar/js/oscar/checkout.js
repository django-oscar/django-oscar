var oscar = oscar || {};
oscar.basket = {
    is_form_being_submitted: false,
    init: function() {
        $('#content_inner').on('click', '#basket_formset a[data-behaviours~="remove"]', function(event) {
            oscar.basket.checkAndSubmit($(this), 'form', 'DELETE');
            event.preventDefault();
        });
        $('#content_inner').on('click', '#basket_formset a[data-behaviours~="save"]', function(event) {
            oscar.basket.checkAndSubmit($(this), 'form', 'save_for_later');
            event.preventDefault();
        });
        $('#content_inner').on('click', '#saved_basket_formset a[data-behaviours~="move"]', function(event) {
            oscar.basket.checkAndSubmit($(this), 'saved', 'move_to_basket');
        });
        $('#content_inner').on('click', '#saved_basket_formset a[data-behaviours~="remove"]', function(event) {
            oscar.basket.checkAndSubmit($(this), 'saved', 'DELETE');
            event.preventDefault();
        });
        $('#content_inner').on('click', '#voucher_form_link a', function(event) {
            oscar.basket.showVoucherForm();
            event.preventDefault();
        });
        $('#content_inner').on('click', '#voucher_form_cancel', function(event) {
            oscar.basket.hideVoucherForm();
            event.preventDefault();
        });
        $('#content_inner').on('submit', '#basket_formset', oscar.basket.submitBasketForm);
        if (window.location.hash == '#voucher') {
            oscar.basket.showVoucherForm();
        }
    },
    submitBasketForm: function(event) {
        $('#messages').html('');
        var payload = $('#basket_formset').serializeArray();
        $.post('/basket/', payload, oscar.basket.submitFormSuccess, 'json');
        event.preventDefault();
    },
    submitFormSuccess: function(data) {
        $('#content_inner').html(data.content_html);
        $('#messages').html('');
        for (var level in data.messages) {
            for (var i=0; i<data.messages[level].length; i++) {
                oscar.messages[level](data.messages[level][i]);
            }
        }
        oscar.basket.is_form_being_submitted = false;
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
