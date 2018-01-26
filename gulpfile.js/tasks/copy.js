var gulp = require("gulp"),
    copyTask = function(cb) {
        gulp.src("node_modules/bootstrap/less/**/*")
            .pipe(gulp.dest("src/oscar/static/oscar/less/bootstrap3"));

        gulp.src("node_modules/bootstrap/dist/js/bootstrap.min.js")
            .pipe(gulp.dest("src/oscar/static/oscar/js/bootstrap3"));

        gulp.src("node_modules/bootstrap/fonts/*")
            .pipe(gulp.dest("src/oscar/static/oscar/fonts/"));
    };

gulp.task("copy", copyTask);
