goog.provide 'app.ui.dropup'

goog.require 'app'
goog.require 'wzk.ui.dropup'

app._app.on '.dropup-button', (element, dom) ->
  wzk.ui.dropup.build element, dom

app._app.on '.navbar-toggle', (element, dom) ->
  wzk.ui.dropup.build element, dom, 250
