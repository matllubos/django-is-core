goog.require 'goog.events'
goog.require 'goog.dom.dataset'
goog.require 'goog.dom.classes'


class app.ui.CopyButton extends wzk.ui.Component

  ###*
    @enum {string} data attrs
  ###
  @DATA:
    COPY_TARGET: 'copyTarget'
    COPIED_MSG: 'copiedMessage'

  ###*
    @param {Object} params
      dom: {@link wzk.dom.Dom}
      zcClass: {Function}
  ###
  constructor: (params) ->
    super params
    {@zcClass, @flash} = params
    @textToCopy = ''
    @zcClient = null
    @copiedMsg = null

  ###*
    @override
  ###
  decorate: (@el) ->
    @copiedMsg = goog.dom.dataset.get @el, app.ui.CopyButton.DATA.COPIED_MSG
    @zcClient = new @zcClass @el
    @textToCopy = @dom.getTextContent @dom.cls(String goog.dom.dataset.get(@el, app.ui.CopyButton.DATA.COPY_TARGET))
    @zcClient['on']('ready', =>
      @zcClient['on']('copy', @handleCopy)
    )

  ###*
    @protected
    @param {Event} e
  ###
  handleCopy: (e) =>
    e['clipboardData']['setData']('text/plain', @textToCopy)
    @flash.addMessage(@copiedMsg, 'success', undefined, true, 1000) if @copiedMsg
