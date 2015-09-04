goog.require 'goog.events'
goog.require 'goog.dom.dataset'
goog.require 'goog.dom.classes'

class app.ui.ScrollToButton extends wzk.ui.Button

  ###*
    @const {string} scroll to element data attr
  ###
  @DATA_SCROLL_TO_EL: 'element'

  ###*
    @const {string} scrolled to el cls
  ###
  @SCROLLED_TO_CLS: 'scrolled-to'

  ###*
    @const {number} scroll to cls remove timeout
  ###
  @SCROLL_TO_REMOVE_TIMEOUT: 2500

  ###*
    @override
  ###
  constructor: (params) ->
    super params
    @scrollToEl = null

  ###*
    @override
  ###
  decorate: (@el) ->
    super @el
    @scrollToEl = @dom.one String(goog.dom.dataset.get @el, app.ui.ScrollToButton.DATA_SCROLL_TO_EL)
    return if not @scrollToEl?

    goog.events.listen @el, goog.events.EventType.CLICK, @handleClick
    return

  ###*
    @param {goog.events.Event} e
  ###
  handleClick: (e) =>
    e.preventDefault()
    return if goog.dom.classes.has @scrollToEl, app.ui.ScrollToButton.SCROLLED_TO_CLS
    new goog.fx.dom.Scroll(@dom.getDocument().body, [0, @dom.getDocumentScroll().y], [0, @scrollToEl.getBoundingClientRect().top], 700).play()
    goog.dom.classes.add @scrollToEl, app.ui.ScrollToButton.SCROLLED_TO_CLS
    removeClsFn = => goog.dom.classes.remove @scrollToEl, app.ui.ScrollToButton.SCROLLED_TO_CLS
    setTimeout removeClsFn , app.ui.ScrollToButton.SCROLL_TO_REMOVE_TIMEOUT
