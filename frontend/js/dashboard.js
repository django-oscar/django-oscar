import '../scss/dashboard.scss';

$(document).ready(function() {
  $('.sidebar__link[href="#"]').on('click', function(e) {
    e.preventDefault();
    openSubmenu(this);
  });
  
  $('.submenu__close').on('click', function(e) {
    e.preventDefault();
    closeSubmenu(this);
  });
  
  function openSubmenu(item) {
    var $parent = $(item).parent();
    $('.sidebar__item').removeClass('open');
    $parent.toggleClass('open');
  }
  
  function closeSubmenu(item) {
    var $parent = $(item).parents('.sidebar__item');
    $parent.removeClass('open');
  }  
});
