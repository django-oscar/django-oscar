/*global opener */
(function() {
    'use strict';
    var initData = JSON.parse(document.getElementById('oscar-popup-response-constants').dataset.popupResponse);
    switch(initData.action) {
    case 'change':
        opener.oscar.dismissChangeRelatedObjectPopup(window, initData.value, initData.obj, initData.new_value);
        break;
    case 'delete':
        opener.oscar.dismissDeleteRelatedObjectPopup(window, initData.value);
        break;
    default:
        opener.oscar.dismissAddRelatedObjectPopup(window, initData.value, initData.obj);
        break;
    }
})();
