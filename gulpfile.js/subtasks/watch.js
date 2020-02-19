const gulp = require('gulp'),
    copy = require('./copy'),
    less = require('./less');

module.exports = function() {
    gulp.watch('src/oscar/static_src/**/*', gulp.series(copy, less));
}
