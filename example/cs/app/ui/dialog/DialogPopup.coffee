goog.require 'goog.dom.dataset'

class app.ui.dialog.DialogPopup extends wzk.ui.dialog.Dialog

  ###*
    @const
    @type {string}
  ###
  @DEFAULT_TITLE: ''

  ###*
    @param {string=} klass
    @param {boolean=} useIframeMask
    @param {wzk.dom.Dom=} dom
  ###
  constructor: (klass, useIframeMask, @dom) ->
    super klass, useIframeMask, @dom
    @setButtonSet wzk.ui.dialog.ButtonSet.createNoYes()
    @listen goog.ui.Dialog.EventType.SELECT, @handleClick

  ###*
    @param {Element} el to decorate
  ###
  decorate: (el) ->
    @setContent(el.innerHTML)

    # extract data link
    @link = goog.dom.dataset.get el, 'link'
    title = goog.dom.dataset.get el, 'title'
    @setTitle(title ? app.ui.dialog.DialogPopup.DEFAULT_TITLE)

    # setup captions
    yesCaption = goog.dom.dataset.get el, 'btnYes'
    noCaption = goog.dom.dataset.get el, 'btnNo'
    @setYesNoCaptions yesCaption, noCaption

  ###*
    @param {goog.events.Event} event
  ###
  handleClick: (event) ->
    if event.key is goog.ui.Dialog.DefaultButtonKeys.YES
      @dom.getWindow().location.assign @link
    else
      @hide()
