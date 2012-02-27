var oscar = oscar || {}
oscar.dashboard = {
    promotions: {
        init: function() {
            $('.promotion_list').sortable({
                handle: '.btn-handle',
                stop: oscar.dashboard.promotions.save_order});
        },
        save_order: function(event, ui) {
            // todo - save order of promotions
            console.log(event, ui);

            // Get the csrf token, otherwise django will not accept the
            // POST request.
            var cookies = document.cookie.split(';');
            var csrf = '';
            $.each(cookies, function(index, cookie) {
                cookie_parts = $.trim(cookie).split('=');
                if (cookie_parts[0] == 'csrftoken') {
                    csrf = cookie_parts[1];
                }
            });
            //ui.csrfmiddlewaretoken = csrf;
            var serial = $(this).sortable("serialize");
            serial = serial + '&csrfmiddlewaretoken=' + csrf;
            $.ajax({
                type: 'POST',
                data: serial,
                dataType: "json",
                url: '#',
                beforeSend: function(xhr, sttngs) {
                    xhr.setRequestHeader("X-CSRFToken", csrf);
                },
            });
        }
    }
}

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
    $(".primary-nav > li > ul:gt(0), .orders_search").hide();

    $(".primary-nav > li > a").click(function()
    {
        $(this).next("ul").slideToggle("fast");
        $(this).toggleClass("viewed");
    });

    //pull out draw
    $(".pull_out").click(function()
    {
        $(this).parent("div").find('.orders_search').slideToggle("fast");
        $(this).toggleClass("viewed");
    });
});
