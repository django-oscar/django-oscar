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
        dateFormat: 'yy-mm-dd',
        datepickerOptions: {},
        datetimepickerOptions: {
            timeFormat: 'HH:mm',
            stepMinute: 15
        },
        init: function() {
            // Run initialisation that should take place on every page of the dashboard.

            // Use datepicker for all inputs that have 'date' or 'datetime' in the name
            if ($.datepicker) {
                o.dashboard.datepickerOptions.dateFormat = o.dashboard.dateFormat;
                $('input[name^="date"], input[name$="date"]').datepicker(o.dashboard.datepickerOptions);
            }
            if ($.ui.timepicker) {
                o.dashboard.datetimepickerOptions.dateFormat = o.dashboard.dateFormat;
                $('input[name$="datetime"]').datetimepicker(o.dashboard.datetimepickerOptions);
            }

            // Use WYSIHTML5 widget on textareas
            var options = {
                "html": true
            };
            $('form.wysiwyg textarea, textarea.wysiwyg').wysihtml5(options);

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
            
            //Adds error icon if there are errors in the product update form
            $('[data-behaviour="affix-nav-errors"] .tab-pane').each(function(){
              var productErrorListener = $(this).find('[class*="error"]').closest('.tab-pane').attr('id');
              $('[data-spy="affix"] a[href="#' + productErrorListener + '"]').append('<i class="icon-info-sign pull-right"></i>');
            });
            
            //Adds type/search for select fields
            $('.form-stacked select, .form-stacked input[data-autocomplete-url]').css('width', '95%');
            $('.form-inline select, .form-inline input[data-autocomplete-url]').css('width', '300px');
            $('select').select2();

            var beauty_select_formaters = {
                result: function (item) {
                    var result = item.text;
                    if (item.image) {
                        result = '<img src="' + item.image + '" /> ' + result;
                    }
                    return result;
                },
                selection: function(item) {
                    return item.text;
                }
            }

            $('input[data-autocomplete-url]').each(function(key, elem){
                var $element = $(elem);
                var data = $element.data();
                var multiple = data['multiple'];
                var allowClear = !data['required'];
                var minimumInputLength = data['minimumInputLength'] || 3;
                var placeholder = data['placeholder'];

                if (data['disabled'] == 'true')
                {
                    $element.select2('disabled');
                } else {
                    var params = {
                        allowClear: allowClear,
                        multiple: multiple,
                        placeholder: placeholder,
                        minimumInputLength: minimumInputLength,
                        formatResult: beauty_select_formaters.result,
                        formatSelection: beauty_select_formaters.selection,
                        initSelection: function(element, callback) {
                            // the input tag has a value attribute preloaded that points to a preselected movie's id
                            // this function resolves that id attribute to an object that select2 can render
                            // using its formatResult renderer - that way the movie name is shown preselected
                            var ids = $element.val();
                            if (ids !== "") {
                                $.ajax(data['autocompleteUrl'], {
                                    data: {
                                        ids: ids
                                    },
                                    dataType: "json"
                                }).done(function(data){
                                        var result = data.result;
                                        var data = data.result;
                                        if (!multiple) {
                                            if (data.length > 0)
                                                data = data[0]
                                        }
                                        callback(data);
                                    });
                            }
                        },
                        ajax: {
                            url: data['autocompleteUrl'],
                            dataType: 'json',
                            quietMillis: 100,
                            data: function (term, page) { // page is the one-based page number tracked by Select2
                                return {
                                    title: term, //search term
                                    page_limit: 20, // page size
                                    page: page // page number
                                };
                            },
                            results: function (data, page) {
                                var more = (page * 20) < data.total; // whether or not there are more results available

                                // notice we return the value of more so Select2 knows if more results can be loaded
                                return {results: data.result, more: more};
                            }
                        }
                    };
                    $element.select2(params);
                }
            });

            o.dashboard.filereader.init();
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
