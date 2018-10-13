var gulp = require('gulp');

gulp.task('watch', function() {
    gulp.watch('src/oscar/static/oscar/less/**/*.less', gulp.parallel('less'));
});
