const gulp = require("gulp");

module.exports = function(done) {
    // Copy all tracked static files into the build directory
    gulp.src("src/oscar/static_src/oscar/**/*")
        .pipe(gulp.dest("src/oscar/static/oscar/"));

    // Copy all third party assets in to the build directory
    gulp.src("node_modules/jquery/dist/jquery.min.js")
        .pipe(gulp.dest("src/oscar/static/oscar/js/jquery"));

    gulp.src([
        "node_modules/bootstrap/dist/js/bootstrap.bundle.js",
        "node_modules/bootstrap/dist/js/bootstrap.bundle.min.js"
    ]).pipe(gulp.dest("src/oscar/static/oscar/js/bootstrap4"));

    gulp.src("node_modules/bootstrap/fonts/*")
        .pipe(gulp.dest("src/oscar/static/oscar/fonts/"));

    gulp.src([
        "node_modules/tempusdominus-bootstrap-4/build/js/*.min.js",
        "node_modules/tempusdominus-bootstrap-4/build/css/*.min.css"
    ]).pipe(gulp.dest("src/oscar/static/oscar/js/bootstrap4-datetimepicker"));

    gulp.src("node_modules/moment/min/moment-with-locales.min.js")
        .pipe(gulp.dest("src/oscar/static/oscar/js/bootstrap4-datetimepicker"));

    gulp.src("node_modules/inputmask/dist/jquery.inputmask.min.js")
        .pipe(gulp.dest("src/oscar/static/oscar/js/inputmask"));

    gulp.src("node_modules/jquery-mousewheel/jquery.mousewheel.js")
        .pipe(gulp.dest("src/oscar/static/oscar/js/mousewheel"));

    gulp.src("node_modules/jquery-sortable/source/js/jquery-sortable-min.js")
        .pipe(gulp.dest("src/oscar/static/oscar/js/jquery-sortable"));

    gulp.src([
        "node_modules/tinymce/**/*.min.js",
        "node_modules/tinymce/**/*.min.css",
        "node_modules/tinymce/**/fonts/*",
        "node_modules/tinymce/**/img/*",
    ]).pipe(gulp.dest("src/oscar/static/oscar/js/tinymce"));

    gulp.src([
        "node_modules/select2/dist/js/select2.min.js",
        "node_modules/select2/dist/css/select2.min.css"
    ]).pipe(gulp.dest("src/oscar/static/oscar/js/select2"));

    gulp.src("node_modules/select2-bootstrap-theme/dist/*.min.css")
        .pipe(gulp.dest("src/oscar/static/oscar/css"));

    gulp.src("node_modules/@fortawesome/fontawesome-free/webfonts/*")
        .pipe(gulp.dest("src/oscar/static/oscar/webfonts"));

    done();
};
