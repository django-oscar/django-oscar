var gulp = require('gulp');

gulp.task('watch', function() {
    var watch = require('gulp-watch');

    gulp.watch('src/oscar/static/oscar/less/**/*.less', ['less']);
});
