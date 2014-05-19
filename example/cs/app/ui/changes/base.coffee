goog.provide 'app.ui.changes'

goog.require 'app.ui.changes.DiscardChanges'
goog.require 'app.ui.changes.DiscardChangesInline'

###*
  @param {Element} el
  @param {wzk.dom.Dom} dom
###
app.ui.changes.decorateDiscardChange = (el, dom) ->
  discard = new app.ui.changes.DiscardChanges undefined, undefined, dom
  discard.decorate el

###*
  @param {Element} el
  @param {wzk.dom.Dom} dom
###
app.ui.changes.decorateDiscardChangeInline = (el, dom) ->
  discard = new app.ui.changes.DiscardChangesInline undefined, undefined, dom
  discard.decorate el


app._app.on '.changed-value .discard-change', (el, dom) ->
  app.ui.changes.decorateDiscardChange el, dom

app._app.on '.changed-new-line .discard-change', (el, dom) ->
  app.ui.changes.decorateDiscardChangeInline el, dom
