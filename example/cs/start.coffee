goog.provide 'app.start'

goog.require 'app'
goog.require 'app.ui'
goog.require 'app.ui.popup'
goog.require 'wzk.ui'

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
