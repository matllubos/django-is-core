goog.provide 'app.ui.dropdown'

goog.require 'app'
goog.require 'app.ui.dropdown.DropDown'

app._app.on '.dropdown-toggle', (el, dom) ->
  dropdown = new app.ui.dropdown.DropDown dom
  dropdown.decorate el
