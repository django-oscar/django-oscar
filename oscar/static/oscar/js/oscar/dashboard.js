var oscar = (function(o, $) {

    o.getCsrfToken = function() {
        // Extract CSRF token from cookies
        var cookies = document.cookie.split(';');
        var csrf_token = null;
        $.each(cookies, function(index, cookie) {
            cookieParts = $.trim(cookie).split('=');
            if (cookieParts[0] == 'csrftoken') {
                csrfToken = cookieParts[1];
            }
        });
        return csrfToken;
    };

    o.dashboard = {
        init: function(options) {
            // Run initialisation that should take place on every page of the dashboard.
            var defaults = {
                'dateFormat': 'yy-mm-dd',
                'timeFormat': 'HH:mm',
                'stepMinute': 15,
                'tinyConfig': {
                    statusbar: false,
                    menubar: false,
                    plugins: "link",
                    style_formats: [
                        {title: 'Heading', block: 'h2'},
                        {title: 'Subheading', block: 'h3'}
                    ],
                    toolbar: "styleselect | bold italic blockquote | bullist numlist | link"
                }
            };
            o.dashboard.options = $.extend(defaults, options);

            o.dashboard.initDatePickers();
            o.dashboard.initWYSIWYG();

            $('.scroll-pane').jScrollPane();

            $(".category-select ul").prev('a').on('click', function(){
                var $this = $(this),
                plus = $this.hasClass('ico_expand');
                if (plus) {
                    $this.removeClass('ico_expand').addClass('ico_contract');
                } else {
                    $this.removeClass('ico_contract').addClass('ico_expand');
                }
                return false;
            });

            // Adds error icon if there are errors in the product update form
            $('[data-behaviour="affix-nav-errors"] .tab-pane').each(function(){
              var productErrorListener = $(this).find('[class*="error"]').closest('.tab-pane').attr('id');
              $('[data-spy="affix"] a[href="#' + productErrorListener + '"]').append('<i class="icon-info-sign pull-right"></i>');
            });

            // Adds type/search for select fields
            $('.form-stacked select').css('width', '95%');
            $('.form-inline select').css('width', '300px');
            $('select').select2({width: 'resolve'});

            o.dashboard.filereader.init();
        },
        initDatePickers: function() {
            // Use datepicker for all inputs that have 'date' or 'datetime' in the name
            if ($.datepicker) {
                var defaultDatepickerConfig = {'dateFormat': o.dashboard.options.dateFormat};
                $('input[name^="date"], input[name$="date"]').each(function(ind, ele) {
                    var $ele = $(ele),
                        config = $.extend({}, defaultDatepickerConfig, {
                            'dateFormat': $ele.data('dateformat')
                        });
                    $ele.datepicker(config);
                });
            }
            if ($.ui.timepicker) {
                var defaultDatetimepickerConfig = {
                    'dateFormat': o.dashboard.options.dateFormat,
                    'timeFormat': o.dashboard.options.timeFormat,
                    'stepMinute': o.dashboard.options.stepMinute
                };
                $('input[name$="datetime"]').each(function(ind, ele) {
                    var $ele = $(ele),
                        config = $.extend({}, defaultDatetimepickerConfig, {
                        'dateFormat': $ele.data('dateformat'),
                        'timeFormat': $ele.data('timeformat'),
                        'stepMinute': $ele.data('stepminute')});
                    $ele.datetimepicker(config);
                });
            }
        },
        initWYSIWYG: function() {
            // Use TinyMCE by default
            $('form.wysiwyg textarea, textarea.wysiwyg').tinymce(o.dashboard.options.tinyConfig);
        },
        offers: {
            init: function() {
                oscar.dashboard.offers.adjustBenefitForm();
                $('#id_type').change(function() {
                    oscar.dashboard.offers.adjustBenefitForm();
                });
            },
            adjustBenefitForm: function() {
                var type = $('#id_type').val(),
                    $valueContainer = $('#id_value').parents('.control-group');
                if (type == 'Multibuy') {
                    $valueContainer.hide();
                } else {
                    $valueContainer.show();
                }
            }
        },
        ranges: {
            init: function() {
                $('[data-behaviours~="remove"]').click(function() {
                    $this = $(this);
                    $this.parents('table').find('input').attr('checked', false);
                    $this.parents('tr').find('input').attr('checked', 'checked');
                    $this.parents('form').submit();
                });
            }
        },
        orders: {
            initTabs: function() {
                if (location.hash) {
                    $('.nav-tabs a[href=' + location.hash + ']').tab('show');
                }
            },
            initTable: function() {
                var table = $('form table'),
                    input = $('<input type="checkbox" />').css({
                        'margin-right': '5px',
                        'vertical-align': 'top'
                    });
                $('th:first', table).prepend(input);
                $(input).change(function(){
                    $('tr', table).each(function() {
                        $('td:first input', this).prop("checked", $(input).is(':checked'));
                    });
                });
            }
        },
        promotions: {
            init: function() {
                $('.promotion_list').sortable({
                    handle: '.btn-handle',
                    stop: o.dashboard.promotions.saveOrder
                });
            },
            saveOrder: function(event, ui) {
                // Get the csrf token, otherwise django will not accept the
                // POST request.
                var serial = $(this).sortable("serialize"),
                    csrf = o.getCsrfToken();
                serial = serial + '&csrfmiddlewaretoken=' + csrf;
                $.ajax({
                    type: 'POST',
                    data: serial,
                    dataType: "json",
                    url: '#',
                    beforeSend: function(xhr, settings) {
                        xhr.setRequestHeader("X-CSRFToken", csrf);
                    }
                });
            }
        },
        search: {
            init: function() {
                var searchForm = $(".orders_search"),
                    searchLink = $('.pull_out'),
                    doc = $('document');
                searchForm.each(function(index) {
                    doc.css('height', doc.height());
                });
                searchLink.on('click', function() {
                    searchForm.parent()
                        .find('.pull-left')
                        .toggleClass('no-float')
                        .end().end()
                        .slideToggle("fast");
                    }
                );
            }
        },
        filereader: {
            init: function() {
                // Add local file loader to update image files on change in
                // dashboard. This will provide a preview to the selected
                // image without uploading it. Upload only occures when
                // submitting the form.
                if (window.FileReader) {
                    $('input[type="file"]').change(function(evt) {
                        var reader = new FileReader();
                        var imgId = evt.target.id + "-image";
                        reader.onload = (function() {
                            return function(e) {
                                var imgDiv = $("#"+imgId);
                                imgDiv.children('img').attr('src', e.target.result);
                            };
                        })();
                        reader.readAsDataURL(evt.target.files[0]);
                    });
                }
            }
        }
    };

    return o;

})(oscar || {}, jQuery);
