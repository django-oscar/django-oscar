var gulp = require('gulp'),
    less = require('gulp-less'),
    sourcemaps = require('gulp-sourcemaps'),
    pump = require('pump'),
    less_task = function(cb) {
        pump([
            gulp.src('src/oscar/static/oscar/less/*.less'),
            sourcemaps.init(),
            less({includePaths: [
                    'src/oscar/static/less/',
                    ],
                    outputStyle: null,
                }),
            sourcemaps.write('/'),
            gulp.dest('src/oscar/static/oscar/css/')
            ],
            cb
        );
    };

gulp.task('less', less_task);
