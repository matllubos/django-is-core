goog.provide 'app.ui.dialog'
goog.require 'app.ui.dialog.DialogPopup'
goog.require 'app.ui.dialog.PreventDialog'

###*
  @param {Element} el to decorate
  @param {wzk.dom.Dom} dom
###
app.ui.dialog.buildDialogPopup =  (el, dom) ->
  dialog = new app.ui.dialog.DialogPopup(undefined, undefined, dom)
  dialog.decorate el

  # whenever dialog is rendered in page, it will be displayed
  dialog.open()
  dialog.focus()

app.ui.dialog.buildConfirmDialog = (el, dom) ->
  dialog = new app.ui.dialog.PreventDialog undefined, undefined, dom
  dialog.watchOn el

app._app.on '.dialog-popup', (element, dom) ->
  app.ui.dialog.buildDialogPopup element, dom

app._app.on '.prevent-dialog', (el, dom) ->
  app.ui.dialog.buildConfirmDialog el, dom
