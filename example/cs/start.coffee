goog.provide 'app.start'

goog.require 'app'
goog.require 'app.ui'
goog.require 'app.ui.popup'
goog.require 'wzk.ui'
goog.require 'app.support.Detector'
goog.require 'app.support.FontDetector'
goog.require 'app.ui.form'

###*
  @param {Window} win
  @param {Object.<string, string>} msgs
###
app.start = (win, msgs) ->

  flash = wzk.ui.buildFlash win.document
  app._app.registerStandardComponents flash

  app._det = new app.support.Detector(win, new app.support.FontDetector(win.document))

  app._app.run win, flash, msgs, {reloadOn403: true}

# ensure the symbol will be visible after compiler renaming
goog.exportSymbol 'app.start', app.start
