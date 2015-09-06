module.exports = (grunt) ->
  {suppe} = require 'grunt-suppe/suppe'

  opts =
    watch_dirs: ['bower_components/werkzeug/wzk/**/']

  suppe grunt, opts
