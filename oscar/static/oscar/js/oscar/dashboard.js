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

            o.dashboard.initWidgets(window.document);

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
              var productErrorListener = $(this).find('[class*="error"]:not(:empty)').closest('.tab-pane').attr('id');
              $('[data-spy="affix"] a[href="#' + productErrorListener + '"]').append('<i class="icon-info-sign pull-right"></i>');
            });

            o.dashboard.filereader.init();
        },
        initWidgets: function(el) {
            /** Attach widgets to form input.
             *
             * This function is called once for the whole page. In that case el is window.document.
             *
             * It is also called when input elements have been dynamically added. In that case el
             * contains the newly added elements.
             *
             * If the element selector refers to elements that may be outside of newly added
             * elements, don't limit to elements within el. Then the operation will be performed
             * twice for these elements. Make sure that that is harmless.
             */
            o.dashboard.initDatePickers(el);
            o.dashboard.initWYSIWYG(el);
            o.dashboard.initSelects(el);
        },
        initSelects: function(el) {
            // Adds type/search for select fields
            $('.form-stacked select:visible').css('width', '95%');
            $('.form-inline select:visible').css('width', '300px');
            $(el).find('select:visible').select2({width: 'resolve'});
            $(el).find('input.select2:visible').each(function(i, e) {
                var opts = {};
                if($(e).data('ajax-url')) {
                    opts = {
                        'ajax': {
                            'url': $(e).data('ajax-url'),
                            'dataType': 'json',
                            'results': function(data, page) {
                                if((page==1) && !($(e).data('required')=='required')) {
                                    data.results.unshift({'id': '', 'text': '------------'});
                                }
                                return data;
                            },
                            'data': function(term, page) {
                                return {
                                    'q': term,
                                    'page': page
                                };
                            }
                        },
                        'multiple': $(e).data('multiple'),
                        'initSelection': function(e, callback){
                            if($(e).val()) {
                                $.ajax({
                                    'type': 'GET',
                                    'url': $(e).data('ajax-url'),
                                    'data': [{'name': 'initial', 'value': $(e).val()}],
                                    'success': function(data){
                                        if(data.results) {
                                            if($(e).data('multiple')){
                                                callback(data.results);
                                            } else {
                                                callback(data.results[0]);
                                            }
                                        }
                                    },
                                    'dataType': 'json'
                                });
                            }
                        }
                    };
                }
                $(e).select2(opts);
            });
        },
        initDatePickers: function(el) {
            // Use datepicker for all inputs that have 'date' or 'datetime' in the name
            if ($.datepicker) {
                var defaultDatepickerConfig = {'dateFormat': o.dashboard.options.dateFormat};
                $(el).find('input[name^="date"]:visible, input[name$="date"]:visible').each(function(ind, ele) {
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
                $(el).find('input[name$="datetime"]:visible').each(function(ind, ele) {
                    var $ele = $(ele),
                        config = $.extend({}, defaultDatetimepickerConfig, {
                        'dateFormat': $ele.data('dateformat'),
                        'timeFormat': $ele.data('timeformat'),
                        'stepMinute': $ele.data('stepminute')});
                    $ele.datetimepicker(config);
                });

                var defaultTimepickerConfig = {
                    'timeFormat': o.dashboard.options.timeFormat,
                    'stepMinute': o.dashboard.options.stepMinute
                };
                $(el).find('input[name$="time"]:visible').not('input[name$="datetime"]').each(function(ind, ele) {
                    var $ele = $(ele),
                        config = $.extend({}, defaultTimepickerConfig, {
                        'timeFormat': $ele.data('timeformat'),
                        'stepMinute': $ele.data('stepminute')});
                    $ele.timepicker(config);
                });
            }
        },
        initWYSIWYG: function(el) {
            // Use TinyMCE by default
            $('form.wysiwyg textarea:visible').tinymce(o.dashboard.options.tinyConfig);
            $(el).find('textarea.wysiwyg:visible').tinymce(o.dashboard.options.tinyConfig);
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
                    $('#id_value').val('');
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
        reordering: (function() {
            var options = {
                handle: '.btn-handle',
                submit_url: '#'
            },
            saveOrder = function(event, ui) {
                // Get the csrf token, otherwise django will not accept the
                // POST request.
                var serial = $(this).sortable("serialize"),
                    csrf = o.getCsrfToken();
                serial = serial + '&csrfmiddlewaretoken=' + csrf;
                $.ajax({
                    type: 'POST',
                    data: serial,
                    dataType: "json",
                    url: options.submit_url,
                    beforeSend: function(xhr, settings) {
                        xhr.setRequestHeader("X-CSRFToken", csrf);
                    }
                });
            },
            init = function(user_options) {
                options = $.extend(options, user_options);
                $(options.wrapper).sortable({
                    handle: options.handle,
                    stop: saveOrder
                });
            };

            return {
                init: init,
                saveOrder: saveOrder
            };
        }()),
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
