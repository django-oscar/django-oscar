/*jslint browser:true */
/*global jQuery, site, console: false */

/*

To register a function against a single break point
---------------------------------------------------
    site.responsive.register(myFunc, 'mobile');

To register a function against several break points
---------------------------------------------------
    site.responsive.register(myFunc, ['mobile', 'tablet']);

To register a function against all break points
---------------------------------------------------
    site.responsive.register(myFunc);

Break points are defined at the end of this file

*/

(function (site, breakPoints, $) {
    "use strict";

    function Responsive() {
        /**
         * a map of names to breakpoints
         *
         * @var object
         */
        var map = {},
        /**
         * a map of names to listener functions
         *
         * @var object
         */
            listeners = {},
        /**
         * a sorted list of break points
         *
         * @var array
         */
            points = [],
        /**
         * The name of the current breakpoint
         *
         * @var string
         */
            current = null;

        /**
         * Get the name of the give breakpoint
         *
         * @param int point
         * @return string
         */
        function getBreakPointName(point) {
            var name;
            for (name in map) {
                if (map.hasOwnProperty(name) && map[name] === point) {
                    return name;
                }
            }
            return null;
        }

        /**
         * Called on document resize
         */
        function checkViewport() {
            var i = 0,
                width = document.body.clientWidth,
                point = points[0],
                breakPoint,
                hasChange,
                funcs;

            for (i = 0; i < points.length; i += 1) {
                if (width >= points[i]) {
                    point = points[i];
                }
            }

            breakPoint = getBreakPointName(point);
            hasChange = (current !== breakPoint);
            current = breakPoint;

            funcs = listeners[current];
            for (i = 0; i < funcs.length; i += 1) {
                funcs[i](hasChange);
            }
        }

        /**
         * Set the breakpoints
         *
         * @param object breaks
         */
        this.setBreakPoints = function (breaks) {
            var name;
            points = [];

            for (name in breaks) {
                if (breaks.hasOwnProperty(name)) {
                    listeners[name] = [];
                    map[name] = breaks[name];
                    points.push(breaks[name]);
                }
            }
            points = points.sort();
        };

        /**
         * Register a function against the named breakpoints
         *
         * breakpoints can be a single breakpoint name or an array of
         * breakpoint names.
         *
         * If breakpoints is not set it will be registered against all
         * breakpoints.
         *
         * @param function func
         * @param mixed breakPoints
         */
        this.register = function (func, breakpoints) {
            var name, i;

            if (typeof breakpoints === 'undefined') {
                breakpoints = [];
                for (name in map) {
                    if (map.hasOwnProperty(name)) {
                        breakpoints.push(name);
                    }
                }
            }
            if (Object.prototype.toString.call(breakpoints) !== '[object Array]') {
                breakpoints = [breakpoints];
            }
            for (i = 0; i < breakpoints.length; i += 1) {
                listeners[breakpoints[i]].push(func);
            }
        };

        /**
         * registers the resize listener
         */
        this.init = function () {
            $(window).resize(function () {
                checkViewport();
            });
            checkViewport();
        };
    }

    var responsive = new Responsive();
    if (typeof breakPoints !== 'undefined') {
        responsive.setBreakPoints(breakPoints);
    }

    site.registerInitFunction(responsive.init);
    site.responsive = responsive;

}(site, {
    'mobile': 0,
    'tablet': 768,
    'desktop': 980
}, jQuery));