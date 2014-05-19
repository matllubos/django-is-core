goog.provide 'app.start'

goog.require 'app'
goog.require 'app.ui'
goog.require 'app.ui.form'
goog.require 'app.ui.grid'
goog.require 'app.ui.inlineform'
goog.require 'app.ui.dropup'
goog.require 'app.ui.dropdown'
goog.require 'app.ui.dialog'
goog.require 'app.ui.zippy'
goog.require 'app.ui.richtooltip'
goog.require 'wzk.ui'
goog.require 'app.ui.tab'
goog.require 'app.ui.changes'
goog.require 'app.ui.chart'
goog.require 'app.ui.report'

###*
  @param {Window} win
  @param {Object.<string, string>} msgs
###
app.start = (win, msgs) ->

  flash = wzk.ui.buildFlash win.document
  app._app.registerStandardComponents flash

  app._app.run win, flash, msgs

# ensure the symbol will be visible after compiler renaming
goog.exportSymbol 'app.start', app.start
