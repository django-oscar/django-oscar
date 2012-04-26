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
    orders: {
        initTabs: function() {
            if (location.hash) {
                $('.nav-tabs a[href=' + location.hash + ']').tab('show');
            }
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
                console.log('asdf');
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
