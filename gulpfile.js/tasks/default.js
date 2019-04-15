var gulp = require('gulp');

gulp.task('default', gulp.series(['copy', 'scss']));
