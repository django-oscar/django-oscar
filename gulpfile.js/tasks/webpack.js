var gulp = require('gulp'),
    util = require('gulp-util'),
    webpack = require('webpack'),
    webpack_config = require('../../webpack.config.js'),
    webpack_task = function(callback) {
        // generate compiled js file
        // and minify if environment == production
        webpack(webpack_config, function(err, stats) {
            if (err) throw new util.PluginError('webpack', err);
            util.log('[webpack]', stats.toString({
                // output options
            }));
            callback();
        });
    };

// used in watch task
gulp.task('webpack', webpack_task);
