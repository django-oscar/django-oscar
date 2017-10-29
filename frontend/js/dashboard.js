import '../scss/dashboard.scss';

$(document).ready(function() {

  // Toggle sidebar menu with Bootstrap
  $('.sidebar__link[href="#"]').on('click', function(e) {
    $(this).dropdown('toggle');
  });

  // Toggle compact sidebar
  $('.navbar__close-sidebar').on('click', function(e) {
    e.preventDefault();
    minimizeSidebar();
  });

  function minimizeSidebar() {
    $('body').toggleClass('compact');
  }
});
