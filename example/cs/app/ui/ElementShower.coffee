goog.require 'goog.dom.dataset'
goog.require 'goog.events'


class app.ui.ElementShower extends wzk.ui.Button

  ###*
    @enum {string} data attrs
  ###
  @DATA:
    TARGET: 'target'

  ###*
    @override
  ###
  constructor: (params = {}) ->
    super params

  ###*
    @override
  ###
  decorate: (@el) ->
    @targetEl = @dom.cls String(goog.dom.dataset.get @el, app.ui.ElementShower.DATA.TARGET)
    if not @targetEl?
      throw new Error 'Target el is not in DOM'
    @dom.hide @targetEl
    goog.events.listen @el, goog.events.EventType.CLICK, @handleClick
    return

  ###*
    @protected
  ###
  handleClick: =>
    @dom.show @targetEl
