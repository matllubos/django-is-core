goog.provide 'app.ui'

goog.require 'app'
goog.require 'wzk.ui.I18NInputDatePicker'
goog.require 'app.ui.ScoreStars'
goog.require 'goog.i18n.DateTimeSymbols_cs'
goog.require 'goog.i18n.DateTimePatterns_cs'
goog.require 'goog.events'
goog.require 'wzk.ui'
goog.require 'wzk.ui.dialog'

goog.require 'app.ui.CountDown'
goog.require 'app.ui.CopyButton'
goog.require 'app.ui.ElementShower'
goog.require 'app.ui.ScrollToButton'

app._app.on 'input[type=datetime], input.datetime, input.date', (el, dom) ->
  goog.i18n.DateTimeSymbols = goog.i18n.DateTimeSymbols_cs
  goog.i18n.DateTimePatterns = goog.i18n.DateTimePatterns_cs
  new wzk.ui.I18NInputDatePicker(dom, "dd'.'MM'.'yyyy").decorate el

app._app.on '.hint', (el, dom) ->
  goog.events.listen el, goog.events.EventType.CLICK, (e) ->
    e.preventDefault()

app._app.on '.field-value.review_score', (el, dom) ->
  new app.ui.ScoreStars(dom).decorate el

app._app.on '.count-down', (el, dom) ->
  new app.ui.CountDown(dom: dom).decorate el

app._app.on '.copy-button-js', (el, dom, xhrFac, opts) ->
  btn = new app.ui.CopyButton zcClass: dom.getWindow()['ZeroClipboard'], dom: dom, flash: opts.flash
  btn.decorate el

app._app.on '.show-element', (el, dom) ->
  shower = new app.ui.ElementShower dom: dom
  shower.decorate el

app._app.on '.snippet-modal', (el, dom, xhrFac, opts) ->
  wzk.ui.dialog.buildSnippetModal el, dom, xhrFac, opts.app.getRegister()

app._app.on '.scroll-to-js', (el, dom) ->
  btn = new app.ui.ScrollToButton dom: dom
  btn.decorate el
