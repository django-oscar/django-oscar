/*jslint browser:true */
/*global jQuery: false */

var site;
(function ($) {
    "use strict";

    site = {
        initList: [],

        init: function () {
            var i;
            for (i = 0; i < site.initList.length; i += 1) {
                site.initList[i]();
            }
        },

        /**
         * Register a function to be called on DOM ready
         *
         * @var function f
         */
        registerInitFunction: function (f) {
            site.initList.push(f);
        }
    };

    $(document).ready(function () {
        site.init();
    });

}(jQuery));