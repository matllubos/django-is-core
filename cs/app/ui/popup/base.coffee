goog.provide 'app.ui.popup'
goog.require 'wzk.ui.popup'

app._app.on '.dropdown', (el, dom) ->
  popup = new wzk.ui.popup.Popup {dom:dom}
  popup.decorate el
