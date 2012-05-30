var oscar = oscar || {};
oscar.basket = {
    is_form_being_submitted: false,
    init: function() {
        $('#basket_formset a[data-behaviours~="remove"]').click(function() {
            oscar.basket.checkAndSubmit($(this), 'DELETE');
        });
        $('#basket_formset a[data-behaviours~="save"]').click(function() {
            oscar.basket.checkAndSubmit($(this), 'save_for_later');
        });
        $('#saved_basket_formset a[data-behaviours~="move"]').click(function() {
            oscar.basket.checkAndSubmit($(this), 'move_to_basket');
        });
        $('#saved_basket_formset a[data-behaviours~="remove"]').click(function() {
            oscar.basket.checkAndSubmit($(this), 'DELETE');
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
    showVoucherForm: function() {
        $('#voucher_form_container').show(); 
        $('#voucher_form_link').hide();
    },
    hideVoucherForm: function() {
        $('#voucher_form_container').hide(); 
        $('#voucher_form_link').show();
    },
    checkAndSubmit: function($ele, idSuffix) {
        if (oscar.basket.is_form_being_submitted) {
            return;
        }
        var formID = $ele.attr('data-id');
        var inputID = '#id_form-' + formID + '-' + idSuffix;
        $(inputID).attr('checked', 'checked');
        $ele.closest('form').submit();
        oscar.basket.is_form_being_submitted = true;
    }
};
oscar.checkout = {
    init: function() {
        // Disable 'place order' button when it is clicked.
        $('#place-order').click(function(e) {
            var $btn = $(this);
            $btn.attr('value', 'Submitting')
                .removeClass('btn-primary')
                .addClass('btn-success');
        });
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
