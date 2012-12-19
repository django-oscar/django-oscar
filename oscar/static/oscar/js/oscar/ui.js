var oscar = oscar || {};
oscar.messages = {
    addMessage: function(tag, msg) {
        var msgHTML = '<div class="alert fade in alert-' + tag + '">' +
        '<a href="#" class="close" data-dismiss="alert">x</a>' + msg +
        '</div>';
        $('#messages').append($(msgHTML));
    },
    debug: function(msg) { oscar.messages.addMessage('debug', msg); },
    info: function(msg) { oscar.messages.addMessage('info', msg); },
    success: function(msg) { oscar.messages.addMessage('success', msg); },
    warning: function(msg) { oscar.messages.addMessage('warning', msg); },
    error: function(msg) { oscar.messages.addMessage('error:', msg); }
};
oscar.promotions = {
    init: function() {
        $('#myCarousel').carousel({
            interval: 6000
        });
    }
};
oscar.notifications = {
    init: function() {
        $('a[data-behaviours~="archive"]').click(function() {
            oscar.notifications.checkAndSubmit($(this), 'archive');
        });
        $('a[data-behaviours~="delete"]').click(function() {
            oscar.notifications.checkAndSubmit($(this), 'delete');
        });
    },
    checkAndSubmit: function($ele, btn_val) {
        $ele.closest('tr').find('input').attr('checked', 'checked');
        $ele.closest('form').find('button[value="' + btn_val + '"]').click();
        return false;
    }
};
oscar.forms = {
    init: function() {
        // Forms with this behaviour are 'locked' once they are submitted to 
        // prevent multiple submissions
        $('form[data-behaviours~="lock"]').submit(oscar.forms.submitIfNotLocked);

        // Disable buttons when they are clicked
        $('.js-disable-on-click').click(function(){$(this).button('loading');});
    },
    submitIfNotLocked: function(event) {
        $form = $(this);
        if ($form.data('locked')) {
            return false;
        }
        $form.data('locked', true);
    }
};
oscar.account = {
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
oscar.catalogue = {
    init: function() {
        // Product star rating -- must improve this in python -- this is 
        // one of the worst things I have ever come across.  It will die in raging fire
        // very soon.
        $('.product_pod, .span6, .promotion_single').each(function() 
        {
            var sum_total_reviews = $(this).find(".review_count li").length * 5,
                sum_rating_count = 0;
            $(this).find('.review_count li').each(function() {
                sum_rating_count += parseFloat($(this).text());
            });
            var ave_rating = sum_rating_count / sum_total_reviews *10;
            if (ave_rating <= 2) {
                ave_rating = 'One';
            } else if (ave_rating <= 4) {
                ave_rating = 'Two';
            } else if (ave_rating <= 6) {
                ave_rating = 'Three';
            } else if (ave_rating <= 8) {
                ave_rating = 'Four';
            } else if (ave_rating <= 10) {
                ave_rating = 'Five';
            }
            $(this).find('.review_count')
                .after('<p class=\"star ' + ave_rating + '\"></p>')
                .remove();
        });
    }
};
oscar.responsive = {
    init: function() {
      var sw = document.body.clientWidth,
          breakpoint = 767,
          mobile = true;
          
      checkMobile();
      
      //Check if Mobile
      function checkMobile() {
        mobile = (sw > breakpoint) ? false : true;
        if (!mobile) { //If Not Mobile
          oscar.responsive.initNav();
          oscar.responsive.initCarousel();
          } else { //Hide 

        }
      }
    },
    initNav: function() {
        var $sidebar = $('aside.span3'), 
            $browse = $('#browse > .dropdown-menu'), 
            $browseOpen = $browse.parent().find('> button[data-toggle]');
        // Set width of nav dropdown on the homepage
        $browse.css('width', $sidebar.outerWidth());
        // Remove click on browse button if menu is currently open
        if ($browseOpen.length < 1) {
            $browse.parent().find('> a').on('click', function() {
                return false;
            });
            // Set margin top of aside allow space for open navigation
            $sidebar.css({
                marginTop: $browse.outerHeight()
            }); 
        }
    },
    initCarousel: function() {
      $('.es-carousel-wrapper').each(function(){
        var gallery = $(this).parent('.rg-thumbs').length,
            galleryCarousel = (gallery > 0) ? true : false;
        //Don't apply this to the gallery carousel    
        if (!galleryCarousel) {
          $(this).elastislide({ 	
            imageW: 175,
            minItems: 4,
            onClick:  true
          });
        }
      });
    }
};
oscar.init = function() {
    oscar.catalogue.init();
    oscar.forms.init();
    oscar.responsive.init();
};
$(function(){oscar.init();});


// TODO - rewrite the below JS to git into the oscar object, splitting the functionality 
// into SRP methods.
$(document).ready(function()
{   
    //For IE - sets the width of a select in an overflow hidden container
    var selectBox = $('.product_pod select'),
        isIE = navigator.userAgent.toLowerCase().indexOf("msie");
    if (isIE > -1) {
      selectBox.on({
        mousedown: function(){
          $(this).addClass("select-open");
        },
        change: function(){
          $(this).removeClass("select-open");
        }
      });
    }
});
