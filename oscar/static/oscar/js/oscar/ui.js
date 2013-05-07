var oscar = (function(o, $) {
    // Replicate Django's flash messages so they can be used by AJAX callbacks.
    o.messages = {
        addMessage: function(tag, msg) {
            var msgHTML = '<div class="alert fade in alert-' + tag + '">' +
                '<a href="#" class="close" data-dismiss="alert">x</a>'  + msg +
                '</div>';
            $('#messages').append($(msgHTML));
        },
        debug: function(msg) { o.messages.addMessage('debug', msg); },
        info: function(msg) { o.messages.addMessage('info', msg); },
        success: function(msg) { o.messages.addMessage('success', msg); },
        warning: function(msg) { o.messages.addMessage('warning', msg); },
        error: function(msg) { o.messages.addMessage('error:', msg); }
    };

    // This block may need removing after reworking of promotions app
    o.promotions = {
        init: function() {
            $('#myCarousel').carousel({
                interval: 6000
            });
        }
    };

    // Notifications inbox within 'my account' section.
    o.notifications = {
        init: function() {
            $('a[data-behaviours~="archive"]').click(function() {
                o.notifications.checkAndSubmit($(this), 'archive');
            });
            $('a[data-behaviours~="delete"]').click(function() {
                o.notifications.checkAndSubmit($(this), 'delete');
            });
        },
        checkAndSubmit: function($ele, btn_val) {
            $ele.closest('tr').find('input').attr('checked', 'checked');
            $ele.closest('form').find('button[value="' + btn_val + '"]').click();
            return false;
        }
    };

    // Site-wide forms events
    o.forms = {
        init: function() {
            // Forms with this behaviour are 'locked' once they are submitted to
            // prevent multiple submissions
            $('form[data-behaviours~="lock"]').submit(o.forms.submitIfNotLocked);

            // Disable buttons when they are clicked
            $('.js-disable-on-click').click(function(){$(this).button('loading');});
        },
        submitIfNotLocked: function(event) {
            var $form = $(this);
            if ($form.data('locked')) {
                return false;
            }
            $form.data('locked', true);
        }
    };

    o.account = {
        init: function() {
            if (document.location.hash) {
                // Ensure the right tab is open if it is specified in the hash.
                var hash = document.location.hash.substring(1),
                $activeClass = $('.account-profile .tabbable'),
                $li = $('a[href=#' + hash + ']').closest('li');
                $activeClass.find('.active').removeClass('active');
                $('#' + hash).add($li).addClass('active');
            }
        }
    };


    o.page = {
        init: function() {
            // Scroll to sections
            $('.top_page a').click(function(e) {
                var href = $(this).attr('href');
                $('html, body').animate({
                    scrollTop: $(href).offset().top
                }, 500);
                e.preventDefault();
            });
            // Tooltips
            $('[rel="tooltip"]').tooltip();
        }
    };

    o.responsive = {
        init: function() {
            if (o.responsive.isDesktop()) {
                o.responsive.initNav();
                o.responsive.initCarousel();
            }
        },
        isDesktop: function() {
            return document.body.clientWidth > 767;
        },
        initNav: function() {
            // Initial navigation for desktop
            var $sidebar = $('aside.span3'), 
                $browse = $('#browse > .dropdown-menu'), 
                $browseOpen = $browse.parent().find('> button[data-toggle]');
            // Set width of nav dropdown to be same as sidebar
            $browse.css('width', $sidebar.outerWidth());
            // Remove click on browse button if menu is currently open
            if (!$browseOpen.length) {
                $browse.parent().find('> a').off('click');
                // Set margin top of aside allow space for open navigation
                $sidebar.css({ marginTop: $browse.outerHeight() });
            }
        },
        initCarousel: function() {
            $('.es-carousel-wrapper').each(function(){
                var gallery = $(this).parent('.rg-thumbs').length;
                // Don't apply this to the gallery carousel
                if (gallery <= 0) {
                    var imageWidth = 175,
                        minProducts = 4;
                    if ($(this).hasClass('wide')) {
                        minProducts = 5;
                    }
                    $(this).elastislide({
                        imageW: imageWidth,
                        minItems: minProducts,
                        onClick: function() {return true;}
                    });
                }
            });
        }
    };

    // IE compabibility hacks
    o.compatibility = {
        init: function() {
            if (!o.compatibility.isIE()) return;
            // Set the width of a select in an overflow hidden container.
            // This is for add-to-basket forms within browing pages
            $('.product_pod select').on({
                mousedown: function(){
                    $(this).addClass("select-open");
                },
                change: function(){
                    $(this).removeClass("select-open");
                }
            });
        },
        isIE: function() {
            return navigator.userAgent.toLowerCase().indexOf("msie") > -1;
        }
    };

    o.basket = {
        is_form_being_submitted: false,
        init: function(options) {
            if (typeof options == 'undefined') {
                options = {'basketURL': document.URL};
            }
            o.basket.url = options.basketURL || document.URL;
            $('#content_inner').on('click', '#basket_formset a[data-behaviours~="remove"]', function(event) {
                o.basket.checkAndSubmit($(this), 'form', 'DELETE');
                event.preventDefault();
            });
            $('#content_inner').on('click', '#basket_formset a[data-behaviours~="save"]', function(event) {
                o.basket.checkAndSubmit($(this), 'form', 'save_for_later');
                event.preventDefault();
            });
            $('#content_inner').on('click', '#saved_basket_formset a[data-behaviours~="move"]', function(event) {
                o.basket.checkAndSubmit($(this), 'saved', 'move_to_basket');
            });
            $('#content_inner').on('click', '#saved_basket_formset a[data-behaviours~="remove"]', function(event) {
                o.basket.checkAndSubmit($(this), 'saved', 'DELETE');
                event.preventDefault();
            });
            $('#content_inner').on('click', '#voucher_form_link a', function(event) {
                o.basket.showVoucherForm();
                event.preventDefault();
            });
            $('#content_inner').on('click', '#voucher_form_cancel', function(event) {
                o.basket.hideVoucherForm();
                event.preventDefault();
            });
            $('#content_inner').on('submit', '#basket_formset', o.basket.submitBasketForm);
            if (window.location.hash == '#voucher') {
                o.basket.showVoucherForm();
            }
        },
        submitBasketForm: function(event) {
            $('#messages').html('');
            var payload = $('#basket_formset').serializeArray();
            $.post(o.basket.url, payload, o.basket.submitFormSuccess, 'json');
            event.preventDefault();
        },
        submitFormSuccess: function(data) {
            $('#content_inner').html(data.content_html);
            $('#messages').html('');
            for (var level in data.messages) {
                for (var i=0; i<data.messages[level].length; i++) {
                    o.messages[level](data.messages[level][i]);
                }
            }
            o.basket.is_form_being_submitted = false;
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
            if (o.basket.is_form_being_submitted) {
                return;
            }
            var formID = $ele.attr('data-id');
            var inputID = '#id_' + formPrefix + '-' + formID + '-' + idSuffix;
            $(inputID).attr('checked', 'checked');
            $ele.closest('form').submit();
            o.basket.is_form_being_submitted = true;
        }
    };

    o.checkout = {
        gateway: {
            init: function() {
                var radioWidgets = $('form input[name=options]');
                o.checkout.gateway.handleRadioSelection(radioWidgets.val());
                radioWidgets.change(o.checkout.gateway.handleRadioChange);
            },
            handleRadioChange: function() {
                o.checkout.gateway.handleRadioSelection($(this).val());
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

    o.init = function() {
        o.forms.init();
        o.page.init();
        o.responsive.init();
        o.compatibility.init();
    };

    return o;

})(oscar || {}, jQuery);
