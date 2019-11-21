const gulp = require('gulp'),
    copy = require('./subtasks/copy'),
    less = require('./subtasks/less')
    watch = require('./subtasks/watch');

module.exports.copy = copy;
module.exports.less = less;
module.exports.watch = watch;
// TODO - these tasks are not running properly in series - less executes before copy has completed.
module.exports.default = gulp.series(copy, less);
