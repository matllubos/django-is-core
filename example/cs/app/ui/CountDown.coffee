goog.require 'goog.dom'
goog.require 'goog.Timer'

goog.require 'wzk.ui.Component'
goog.require 'wzk.num'

class app.ui.CountDown extends wzk.ui.Component

  ###*
    @const {number} interval
  ###
  @INTERVAL: 1000

  ###*
    @param {Object} params
      dom: {@link wzk.dom.Dom}
  ###
  constructor: (params) ->
    super params
    @timer = new goog.Timer app.ui.CountDown.INTERVAL
    @timer.listen goog.Timer.TICK, @ticked
    @base = 0

  ###*
    @override
  ###
  decorate: (@el) ->
    @base = wzk.num.parseDec goog.dom.getTextContent el
    return if not @base?
    super @el
    @timer.start()

  ###*
    @protected
  ###
  ticked: =>
    @base--
    goog.dom.setTextContent @el, @base
    @timer.stop() if @base <= 0
