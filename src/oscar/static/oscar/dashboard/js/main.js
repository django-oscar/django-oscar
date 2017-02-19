import '../scss/main.scss';
import $ from 'jquery';
var bootstrap = require('bootstrap-sass/assets/javascripts/bootstrap.js');
var moment = require('moment');
import Chart from 'chart.js'


$('[data-toggle="sidebar"]').click(function() {
  $('body').toggleClass('nav-open')
});

for (var i=0; i < window.init_queue.length; i++) {
  window.init_queue[i]();
}
