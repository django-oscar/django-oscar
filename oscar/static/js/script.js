/* Author: 

*/
$(document).ready(function()
{	

  // Product star rating  -- must improve this in python
  $('.product_pod, .span6').each(function() 
  {
    var sum_total_reviews = $(this).find(".review_count li").length * 5;
    var sum_rating_count = 0;
    $(this).find('.review_count li').each(function() 
    {
      sum_rating_count += parseFloat($(this).text());
    });
    var ave_rating = sum_rating_count / sum_total_reviews *10;
    if (ave_rating <= 2) {
      var ave_rating = 'One'
    }
    else if (ave_rating <= 4) {
      var ave_rating = 'Two'
    }
    else if (ave_rating <= 6) {
      var ave_rating = 'Three'
    }
    else if (ave_rating <= 8) {
      var ave_rating = 'Four'
    }
    else if (ave_rating <= 10) {
      var ave_rating = 'Five'
    }
    $(this).find('.review_count').after('<p class=\"star ' + ave_rating + '\">' + ave_rating + ' star(s) by user reviews. <a href=\"#\">Add review</a></p>');
    $(this).find('.review_count').remove();
  });
  // Product star rating each review -- must improve this in python
  $('.review').each(function()
  {
    var user_rating = 0;
    $(this).find('span').each(function() 
    {
      user_rating += parseFloat($(this).text());
    });
    if (user_rating == 1) {
      var user_rating = 'One'
    }
    else if (user_rating == 2) {
      var user_rating = 'Two'
    }
    else if (user_rating == 3) {
      var user_rating = 'Three'
    }
    else if (user_rating == 4) {
      var user_rating = 'Four'
    }
    else if (user_rating == 5) {
      var user_rating = 'Five'
    }
    $(this).find('h3').addClass(user_rating);
    $(this).find('span').remove();
  });

  // For multiple submenus in drop down menus
  var u = $('ul.nav li ul li ul, ul.tabs li ul li ul,').length;
  if (u > 0) {
    $("ul.nav li").hover(function()
    {
      $(this).addClass("hover");
      $('ul:first',this).css('visibility', 'visible');
    }, function(){
      $(this).removeClass("hover");
      $('ul:first',this).css('visibility', 'hidden');
    });
    $("ul.nav li ul li:has(ul), ul.tabs li ul li:has(ul)").find("a:first").append(" &raquo; ");
  }
  
  // This activates elastislide
  $('#carousel').elastislide({
    imageW 	: 200,
    minItems	: 4
  });
  
  // Acordion - remove the first in the list as it is duplication.
  var n = $('.accordion dt').length;
  if (n > 1) {
    $('.accordion dt:first, .accordion dd:first,').hide();
  }
  // Acordion
  $('.accordion dd').each(function(index) 
  {
    $(this).css('height', $(this).height());
  });
  $(".accordion dt").click(function(){
    $(this).next("dd").slideToggle("slow")
    .siblings("dd:visible").slideUp("slow");
    $(this).toggleClass("open");
    $(this).siblings("dt").removeClass("open");
  });
  $(".accordion dd").hide();
  
  //scrollto function
  var $scrollpage = $('body');
  $('.span6 .star, .span6 .star a').click(function(){
  	$scrollpage.stop().scrollTo( $('.review_read'), 1000 );
  	return false;
  });
  $('a.read_decription').click(function(){
  	$scrollpage.stop().scrollTo( $('.sub-header'), 1000 );
  	return false;
  });
  $('.top_page a').click(function(){
  	$scrollpage.stop().scrollTo( $('body'), 1000 );
  	return false;
  });
  
  
});
