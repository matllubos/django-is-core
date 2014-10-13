module.exports = (grunt) ->
  {suppe} = require 'grunt-suppe/suppe'

  bower = 'bower_components'

  opts =
    watch_dirs: ['bower_components/werkzeug/wzk/**/']
    app_compiled_output_path: 'static/js/cl-app.js'
    overridden_config:
      concat:
        option:
          separator: ';'
        dist:
          src: ["#{bower}/d3/d3.min.js", 'static/js/c3.js', 'static/js/cl-app.js']
          dest: 'static/js/app.js'
    externs: [
      'bower_components/c3-externs/c3-externs.js'
    ]

  suppe grunt, opts

  grunt.loadNpmTasks 'grunt-contrib-concat'

  grunt.registerTask 'dist', 'Build JS for a production mode', ->
    grunt.task.run ['build', 'concat']
