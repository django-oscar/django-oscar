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
    //table font size increase decrease
    $('.fontsize li').click(function()
    {
        var os = $('.bordered-table').css('font-size');// find font size for p
        var uom = os.slice(-2);// finds the unit of mesure = pixles
        var num = parseFloat(os, 10);// gets rid of the px
        $('.bordered-table').css('font-size', num / 1.1 + uom);
        if (this.id == 'larger') {
            $('.bordered-table').css('font-size', num * 1.1 + uom);
        }
    });

    //side navigation accordion
    $('.primary-nav > li > ul, .orders_search').each(function(index)
    {
        $(this).css('height', $(this).height());
    });
    $(".primary-nav > li > ul, .orders_search").hide();

    $(".primary-nav > li > a").click(function()
    {
        $(this).next("ul").slideToggle("fast");
        $(this).toggleClass("viewed");
    });

    //pull out draw
    $(".pull_out").click(function()
    {
        $('.orders_search').slideToggle("fast");
        $(this).toggleClass("viewed");
    });
    

});
