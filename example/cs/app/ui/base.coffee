goog.provide 'app.ui'

goog.require 'app'
goog.require 'wzk.ui.I18NInputDatePicker'
goog.require 'goog.i18n.DateTimeSymbols_cs'
goog.require 'goog.i18n.DateTimePatterns_cs'
goog.require 'wzk.ui'

app._app.on 'input[type=datetime], input.datetime, input.date', (el, dom) ->
  goog.i18n.DateTimeSymbols = goog.i18n.DateTimeSymbols_cs
  goog.i18n.DateTimePatterns = goog.i18n.DateTimePatterns_cs
  new wzk.ui.I18NInputDatePicker(dom, "dd'.'MM'.'yyyy").decorate el
