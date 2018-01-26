var gulp = require('gulp'),
    concat = require('gulp-concat');
    copy_task = function(cb) {
        gulp.src('node_modules/jquery/dist/jquery.min.js')
            .pipe(gulp.dest('src/oscar/static/oscar/js/jquery'));

        gulp.src('node_modules/bootstrap/less/**/*')
            .pipe(gulp.dest('src/oscar/static/oscar/less/bootstrap3'));

        gulp.src('node_modules/bootstrap/dist/js/bootstrap.min.js')
            .pipe(gulp.dest('src/oscar/static/oscar/js/bootstrap3'));

        gulp.src([
            'node_modules/bootstrap-datetime-picker/js/*.min.js',
            'node_modules/bootstrap-datetime-picker/css/*.min.css'
        ]).pipe(gulp.dest('src/oscar/static/oscar/js/bootstrap-datetimepicker'));

        // Concatenate all timepicker locales into a single file
        gulp.src('node_modules/bootstrap-datetime-picker/js/locales/*')
            .pipe(concat('all-locales.js'))
            .pipe(gulp.dest('src/oscar/static/oscar/js/bootstrap-datetimepicker'));

        gulp.src('node_modules/jquery.inputmask/dist/jquery.inputmask.bundle.js')
            .pipe(gulp.dest('src/oscar/static/oscar/js/inputmask'));

        gulp.src('node_modules/jquery-sortable/source/js/jquery-sortable-min.js')
            .pipe(gulp.dest('src/oscar/static/oscar/js/jquery-sortable'));

        gulp.src('node_modules/jquery-mousewheel/jquery.mousewheel.js')
            .pipe(gulp.dest('src/oscar/static/oscar/js/mousewheel'));

        gulp.src([
            'node_modules/select2/dist/js/select2.min.js',
            'node_modules/select2/dist/css/select2.min.css'
        ]).pipe(gulp.dest('src/oscar/static/oscar/js/select2'));

        gulp.src('node_modules/select2-bootstrap-theme/dist/*.min.css')
            .pipe(gulp.dest('src/oscar/static/oscar/css'));
    };

gulp.task('copy', copy_task);
