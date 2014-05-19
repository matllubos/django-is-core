goog.require 'goog.dom.forms'
goog.require 'wzk.ui.ButtonRenderer'
goog.require 'goog.dom.classes'
goog.require 'goog.dom.dataset'
goog.require 'goog.fx.dom.FadeOutAndHide'
goog.require 'goog.fx.Transition.EventType'

class app.ui.changes.AbstractDiscardChanges extends goog.ui.Button

  ###*
    @enum {string}
  ###
  @DATA:
    VALUE: 'value'
    FOR: 'for'

  ###*
    @enum {string}
  ###
  @CLS:
    NOT_DISCARDED: 'not-discarded'
    CHANGED_VALUE: 'changed-value'
    CHECK: 'discard-check'

  ###*
    @param {goog.ui.ControlContent=} content
    @param {goog.ui.ButtonRenderer=} renderer
    @param {goog.dom.DomHelper=} dom
  ###
  constructor: (content, renderer, dom) ->
    renderer ?= wzk.ui.ButtonRenderer.getInstance()
    super content, renderer, dom
    @fields = []
    @origValEl = null
    @val = ''
    @parent = null
    @grandParent = null
    @wrappers = []
    @toDisappear = null

  ###*
    @override
  ###
  decorateInternal: (el) ->
    @setElementInternal el

    @decorateChanges()

    @wrappers.push @grandParent
    @listen goog.ui.Component.EventType.ACTION, @handleAction
    undefined

  ###*
    @protected
    @return {*}
  ###
  decorateChanges: ->

  ###*
    @protected
  ###
  handleAction: ->
    goog.dom.forms.setValue f, @val for f in @fields
    @fadeOutTrigger()

  ###*
    @protected
    @return {Array}
  ###
  getOrigValues: ->
    @getOrigValue el for el in @dom_.getChildren @origValEl

  ###*
    @protected
    @return {string}
  ###
  getOrigValueForInput: ->
    @getOrigValues().pop()

  ###*
    @protected
    @param {Element} el
    @return {string}
  ###
  getOrigValue: (el) ->
    String goog.dom.dataset.get(el, app.ui.changes.AbstractDiscardChanges.DATA.VALUE)

  ###*
    @protected
  ###
  fadeOutTrigger: =>
    anim = new goog.fx.dom.FadeOutAndHide @toDisappear, 1000
    anim.listen goog.fx.Transition.EventType.END, =>
      goog.dom.classes.remove el, app.ui.changes.AbstractDiscardChanges.CLS.NOT_DISCARDED for el in @wrappers
      undefined
    anim.play()
