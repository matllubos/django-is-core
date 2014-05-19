goog.require 'goog.dom.dataset'
goog.require 'goog.events'
goog.require 'goog.ui.Dialog.EventType'

class app.ui.dialog.PreventDialog extends wzk.ui.dialog.Dialog

  @DATA:
    TITLE: 'confirmTitle'
    CONFIRM: 'confirm'
    BTN_YES: 'btnYes'
    BTN_NO: 'btnNo'
    HREF: 'href'

  ###*
    @param {string=} klass
    @param {boolean=} useIframeMask
    @param {wzk.dom.Dom=} dom
  ###
  constructor: (klass, useIframeMask, dom) ->
    super klass, useIframeMask, dom
    @link = ''
    @el = null

  ###*
    @param {Element} el
  ###
  watchOn: (@el) ->
    D = app.ui.dialog.PreventDialog.DATA

    @link = goog.dom.dataset.get(el, D.HREF) ? el.href

    @setContent String goog.dom.dataset.get el, D.CONFIRM

    @setTitle String goog.dom.dataset.get el, D.TITLE

    btnYes = goog.dom.dataset.get(el, D.BTN_YES)
    btnNo = goog.dom.dataset.get(el, D.BTN_NO)
    @setYesNoCaptions btnYes, btnNo

    goog.events.listen el, goog.events.EventType.CLICK, @handleClick

    @listen goog.ui.Dialog.EventType.SELECT, @handleBtns

  ###*
    @protected
    @param {goog.events.Event} e
  ###
  handleClick: (e) =>
    e.preventDefault()
    @open()
    @focus()

  ###*
    @protected
  ###
  applyDefault: =>
    if @link
      @dom_.getWindow().location.assign @link
    else if @el.form?.submit?
      @el.form.submit()

  ###*
    @protected
    @param {goog.events.Event} e
  ###
  handleBtns: (e) =>
    if e.key is goog.ui.Dialog.DefaultButtonKeys.YES
      @applyDefault()
    else
      @hide()
