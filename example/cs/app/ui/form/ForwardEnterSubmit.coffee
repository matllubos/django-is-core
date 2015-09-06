goog.require 'goog.events'

class app.ui.form.ForwardEnterSubmit

  ###*
    @param {wzk.dom.Dom} dom
  ###
  constructor: (@dom) ->
    @forwardTo = null

  ###*
    @param {Element} formEl
    @param {Element} forwardTo
  ###
  forward: (formEl, @forwardTo) ->
    goog.events.listen formEl, [goog.events.EventType.KEYPRESS], @handleKeyPress if @forwardTo?

  ###*
    @protected
  ###
  handleKeyPress: (e) =>
    if e.keyCode is goog.events.KeyCodes.ENTER
      @forwardTo.click()
      e.preventDefault()
