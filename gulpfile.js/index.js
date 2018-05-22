var requireDir = require('require-dir');
requireDir('./subtasks', { recurse: true });
requireDir('./tasks', { recurse: false });
