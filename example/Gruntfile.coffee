module.exports = (grunt) ->
  {suppe} = require 'grunt-suppe/suppe'

  bower = 'bower_components'

  opts =
    watch_dirs: ['bower_components/werkzeug/wzk/**/']
    app_compiled_output_path: 'static/js/cl-app.js'
    overridden_config:
      uglify:
        my_target:
          files:
            'var/bower_components/d3-tip/d3-tip.min.js': ["#{bower}/d3-tip/index.js"]

      concat:
        option:
          separator: ';'
        dist:
          src: ["#{bower}/d3/d3.min.js", "var/#{bower}/d3-tip/d3-tip.min.js", 'static/js/cl-app.js']
          dest: 'static/js/app.js'

  suppe grunt, opts

  grunt.loadNpmTasks 'grunt-contrib-uglify'
  grunt.loadNpmTasks 'grunt-contrib-concat'

  grunt.registerTask 'dist', 'Build JS for a production mode', ->
    grunt.task.run ['build', 'uglify', 'concat']
