var gulp = require('gulp'),
    sass = require('gulp-sass'),
    sourcemaps = require('gulp-sourcemaps'),
    pump = require('pump'),
    scss_task = function(cb) {
        pump([
            gulp.src('src/oscar/static_src/oscar/scss/*.scss'),
            sourcemaps.init(),
            sass({includePaths: [
                    'src/oscar/static_src/oscar/scss/',
                    ],
                    outputStyle: null,
                }),
            sourcemaps.write('/'),
            gulp.dest('src/oscar/static/oscar/css/')
            ],
            cb
        );
    };

gulp.task('scss', scss_task);
