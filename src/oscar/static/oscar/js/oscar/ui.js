var oscar = (function(o, $) {
    // Replicate Django's flash messages so they can be used by AJAX callbacks.
    o.messages = {
        addMessage: function(tag, msg) {
            var msgHTML = '<div class="alert fade in alert-' + tag + '">' +
                '<a href="#" class="close" data-dismiss="alert">&times;</a>'  + msg +
                '</div>';
            $('#messages').append($(msgHTML));
        },
        debug: function(msg) { o.messages.addMessage('debug', msg); },
        info: function(msg) { o.messages.addMessage('info', msg); },
        success: function(msg) { o.messages.addMessage('success', msg); },
        warning: function(msg) { o.messages.addMessage('warning', msg); },
        error: function(msg) { o.messages.addMessage('danger', msg); },
        clear: function() {
            $('#messages').html('');
        },
        scrollTo: function() {
            $('html').animate({scrollTop: $('#messages').offset().top});
        }
    };

    o.search = {
        init: function() {
            o.search.initSortWidget();
            o.search.initFacetWidgets();
        },
        initSortWidget: function() {
            // Auto-submit (hidden) search form when selecting a new sort-by option
            $('#id_sort_by').on('change', function() {
                $(this).closest('form').submit();
            });
        },
        initFacetWidgets: function() {
            // Bind events to facet checkboxes
            $('.facet_checkbox').on('change', function() {
                window.location.href = $(this).next('.facet_url').val();
            });
        }
    };

    // This block may need removing after reworking of promotions app
    o.promotions = {
        init: function() {

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

            // Disable buttons when they are clicked and show a "loading" message taken from the
            // data-loading-text attribute (http://getbootstrap.com/2.3.2/javascript.html#buttons).
            // Do not disable if button is inside a form with invalid fields.
            // This uses a delegated event so that it keeps working for forms that are reloaded
            // via AJAX: https://api.jquery.com/on/#direct-and-delegated-events
            $(document.body).on('click', '[data-loading-text]', function(){
                var form = $(this).parents("form");
                if (!form || $(":invalid", form).length == 0)
                    $(this).button('loading');
            });
            // stuff for star rating on review page
            // show clickable stars instead of a select dropdown for product rating
            ratings = $('.reviewrating');
            if(ratings.length){
                ratings.find('.star-rating i').on('click',o.forms.reviewRatingClick);
            }
        },
        submitIfNotLocked: function(event) {
            var $form = $(this);
            if ($form.data('locked')) {
                return false;
            }
            $form.data('locked', true);
        },
        reviewRatingClick: function(event){
            var ratings = ['One','Two','Three','Four','Five']; //possible classes for display state
            $(this).parent().removeClass('One Two Three Four Five').addClass(ratings[$(this).index()]);
            $(this).closest('.controls').find('select').val($(this).index() + 1); //select is hidden, set value
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
            }
        },
        isDesktop: function() {
            return document.body.clientWidth > 767;
        },
        initNav: function() {
            // Initial navigation for desktop
            var $sidebar = $('aside.col-sm-3'),
                $browse = $('[data-navigation="dropdown-menu"]'),
                $browseOpen = $browse.parent().find('> a[data-toggle]');
            // Set width of nav dropdown to be same as sidebar
            $browse.css('width', $sidebar.outerWidth());
            // Remove click on browse button if menu is currently open
            if (!$browseOpen.length) {
                $browse.parent().find('> a').off('click');
                // Set margin top of aside allow space for open navigation
                $sidebar.css({ marginTop: $browse.outerHeight() });
            }
        },
        initSlider: function() {
            $('.carousel').carousel({
                interval: 20000
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
            if (event) {
                event.preventDefault();
            }
        },
        submitFormSuccess: function(data) {
            $('#content_inner').html(data.content_html);

            // Show any flash messages
            o.messages.clear();
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
            $('#id_code').focus();
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
                var selectedRadioWidget = $('form input[name=options]:checked');
                o.checkout.gateway.handleRadioSelection(selectedRadioWidget.val());
                radioWidgets.change(o.checkout.gateway.handleRadioChange);
                $('#id_username').focus();
            },
            handleRadioChange: function() {
                o.checkout.gateway.handleRadioSelection($(this).val());
            },
            handleRadioSelection: function(value) {
                var pwInput = $('#id_password');
                if (value == 'anonymous' || value =='new') {
                    pwInput.attr('disabled', 'disabled');
                } else {
                    pwInput.removeAttr('disabled');
                }
            }
        }
    };

    o.datetimepickers = {
        init: function() {
            o.datetimepickers.initDatePickers(window.document);
        },
        options: {
            'languageCode': 'en',
            'dateFormat': 'yy-mm-dd',
            'timeFormat': 'hh:ii',
            'datetimeFormat': 'yy-mm-dd hh:ii',
            'stepMinute': 15,
        },
        initDatePickers: function(el) {
            if ($.fn.datetimepicker) {
                var defaultDatepickerConfig = {
                    'format': o.datetimepickers.options.dateFormat,
                    'autoclose': true,
                    'language': o.datetimepickers.options.languageCode,
                    'minView': 2
                };
                $dates = $(el).find('[data-oscarWidget="date"]').not('.no-widget-init').not('.no-widget-init *');
                $dates.each(function(ind, ele) {
                    var $ele = $(ele),
                        config = $.extend({}, defaultDatepickerConfig, {
                            'format': $ele.data('dateformat')
                        });
                    $ele.datetimepicker(config);
                });

                var defaultDatetimepickerConfig = {
                    'format': o.datetimepickers.options.datetimeFormat,
                    'minuteStep': o.datetimepickers.options.stepMinute,
                    'autoclose': true,
                    'language': o.datetimepickers.options.languageCode
                };
                $datetimes = $(el).find('[data-oscarWidget="datetime"]').not('.no-widget-init').not('.no-widget-init *');
                $datetimes.each(function(ind, ele) {
                    var $ele = $(ele),
                        config = $.extend({}, defaultDatetimepickerConfig, {
                          'format': $ele.data('datetimeformat'),
                          'minuteStep': $ele.data('stepminute')
                        });
                    $ele.datetimepicker(config);
                });

                var defaultTimepickerConfig = {
                    'format': o.datetimepickers.options.timeFormat,
                    'minuteStep': o.datetimepickers.options.stepMinute,
                    'autoclose': true,
                    'language': o.datetimepickers.options.languageCode
                };
                $times = $(el).find('[data-oscarWidget="time"]').not('.no-widget-init').not('.no-widget-init *')
                $times.each(function(ind, ele) {
                    var $ele = $(ele),
                        config = $.extend({}, defaultTimepickerConfig, {
                          'format': $ele.data('timeformat'),
                          'minuteStep': $ele.data('stepminute'),
                          'startView': 1,
                          'maxView': 1,
                          'formatViewType': 'time'
                        });
                    $ele.datetimepicker(config);
                });
            }
        }
    };


    o.init = function() {
        o.forms.init();
        o.datetimepickers.init();
        o.page.init();
        o.responsive.init();
        o.responsive.initSlider();
        o.compatibility.init();
    };

    return o;

})(oscar || {}, jQuery);
