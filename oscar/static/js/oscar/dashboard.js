var oscar = oscar || {};
oscar.get_csrf_token = function() {
    var cookies = document.cookie.split(';');
    $.each(cookies, function(index, cookie) {
        cookie_parts = $.trim(cookie).split('=');
        if (cookie_parts[0] == 'csrftoken') {
            return cookie_parts[1];
        }
    });
    return null;
};
oscar.dashboard = {
    promotions: {
        init: function() {
            $('.promotion_list').sortable({
                handle: '.btn-handle',
                stop: oscar.dashboard.promotions.save_order});
        },
        save_order: function(event, ui) {
            // Get the csrf token, otherwise django will not accept the
            // POST request.
            var serial = $(this).sortable("serialize"),
                csrf = oscar.get_csrf_token();
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
    }
};

$(document).ready(function()
{
    //pull out draw
    var 
      pull_out_draw = $(".orders_search"),
      pull_out_link = $('.pull_out'),
      $this = $(this);

    pull_out_draw.each(function(index)
    {
      $this.css('height', $this.height());
    });
    pull_out_draw.hide();  
    pull_out_link.on('click', function()
    {
      pull_out_draw
        .parent()      
        .find('.pull-left')
        .toggleClass('no-float')
        .end().end()
        .slideToggle("fast");
    });
});
