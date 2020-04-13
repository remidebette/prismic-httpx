var gulp = require('gulp'),
    gist = require('gulp-gist'),
    deploy = require("gulp-gh-pages");

var pkg = require('./package.json');

gulp.task('deploy:doc', function () {
    return gulp.src("./docs/**/*")
        .pipe(deploy());
});

gulp.task('deploy:gist', function () {

    gulp.src("./tests/test_doc.py")
        .pipe(gist());
});

gulp.task('dist', gulp.series(['deploy:doc', 'deploy:gist']));

/**
 * Default task
 */

gulp.task('default', gulp.series('deploy:gist'));

