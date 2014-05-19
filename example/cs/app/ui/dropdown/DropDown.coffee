goog.require 'goog.events'
goog.require 'goog.events.EventType'

class app.ui.dropdown.DropDown

  ###*
    @enum {string}
  ###
  @CLS:
    OPEN: 'open'

  ###*
    @enum {string}
  ###
  @DATA:
    TOGGLE: 'toggle'

  ###*
    @param {wzk.dom.Dom} dom
  ###
  constructor: (@dom) ->
    @toggleList = null
    @parent = null

  ###*
    @param {Element} el
  ###
  decorate: (el) ->
    @toggleEl = @dom.getElement String goog.dom.dataset.get el, app.ui.dropdown.DropDown.DATA.TOGGLE
    return unless @toggleEl?
    @parent = @dom.getParentElement @toggleEl
    goog.events.listen el, goog.events.EventType.CLICK, @handleToggle
    goog.events.listen el, goog.events.EventType.BLUR, @handleBlur

  ###*
    @protected
  ###
  handleToggle: =>
    goog.dom.classes.add @parent, app.ui.dropdown.DropDown.CLS.OPEN

  ###*
    @protected
  ###
  handleBlur: =>
    hide = =>
      goog.dom.classes.remove @parent, app.ui.dropdown.DropDown.CLS.OPEN
    setTimeout hide, 250
