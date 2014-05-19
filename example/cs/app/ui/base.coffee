goog.provide 'app.ui'

goog.require 'wzk.ui.I18NInputDatePicker'
goog.require 'goog.i18n.DateTimeSymbols_cs'
goog.require 'goog.i18n.DateTimePatterns_cs'
goog.require 'wzk.ui'

###*
  @param {Element} el
  @param {wzk.dom.Dom} dom
###
app.ui.navbarToggle = (el, dom) ->
  goog.events.listen el, 'click', ->
    goog.dom.classes.toggle el, 'collapsed'

    target = goog.dom.dataset.get el, 'target'
    menu = dom.cls String target
    goog.dom.classes.toggle menu, 'in'

app.ui.listToggle = (el, dom) ->
  goog.events.listen el, 'click', ->
    goog.dom.classes.toggle el, 'opened'

app._app.on 'input[type=datetime], input.datetime, input.date', (el, dom) ->
  goog.i18n.DateTimeSymbols = goog.i18n.DateTimeSymbols_cs
  goog.i18n.DateTimePatterns = goog.i18n.DateTimePatterns_cs
  new wzk.ui.I18NInputDatePicker(dom, "dd'.'MM'.'yyyy").decorate el

app._app.on 'input.date-simple', (el, dom) ->
  goog.i18n.DateTimeSymbols = goog.i18n.DateTimeSymbols_cs
  goog.i18n.DateTimePatterns = goog.i18n.DateTimePatterns_cs
  new wzk.ui.I18NInputDatePicker(dom, "dd'.'MM", {useSimpleNavigationMenu: true}).decorate el

app._app.on '.navbar-toggle', (el, dom) ->
  app.ui.navbarToggle el, dom

app._app.on '*[data-snippet-onload]', (el, dom, xhrFac) ->
  wzk.ui.loadSnippet el, dom, xhrFac

app._app.on '.report ul > li', (el, dom) ->
  app.ui.listToggle el, dom
