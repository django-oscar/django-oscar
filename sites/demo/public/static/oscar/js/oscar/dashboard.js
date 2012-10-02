var oscar = oscar || {};
oscar.getCsrfToken = function() {
    var cookies = document.cookie.split(';');
    var csrf_token = null;
    $.each(cookies, function(index, cookie) {
        cookieParts = $.trim(cookie).split('=');
        if (cookie_parts[0] == 'csrftoken') {
            csrfToken = cookieParts[1];
        }
    });
    return csrfToken;
};
oscar.dashboard = {
    init: function() {
        $('input[name^="date"], input[name$="date"]').datepicker({dateFormat: 'yy-mm-dd'});
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
                stop: oscar.dashboard.promotions.saveOrder
            });
        },
        saveOrder: function(event, ui) {
            // Get the csrf token, otherwise django will not accept the
            // POST request.
            var serial = $(this).sortable("serialize"),
                csrf = oscar.getCsrfToken();
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
    }
};
