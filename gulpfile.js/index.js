const gulp = require('gulp');
const copy = require('./subtasks/copy');
const scss = require('./subtasks/scss');
const watch = require('./subtasks/watch');

module.exports.copy = copy;
module.exports.scss = scss;
module.exports.watch = watch;
// TODO - these tasks are not running properly in series - scss executes before copy has completed.
// module.exports.default = gulp.series(copy, scss);
