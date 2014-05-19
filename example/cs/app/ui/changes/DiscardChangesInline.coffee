goog.require 'goog.dom.forms'
goog.require 'wzk.ui.ButtonRenderer'
goog.require 'goog.dom.classes'
goog.require 'goog.dom.dataset'
goog.require 'goog.fx.dom.FadeOutAndHide'
goog.require 'goog.fx.Transition.EventType'

class app.ui.changes.DiscardChangesInline extends app.ui.changes.AbstractDiscardChanges

  ###*
    @param {goog.ui.ControlContent=} content
    @param {goog.ui.ButtonRenderer=} renderer
    @param {goog.dom.DomHelper=} dom
  ###
  constructor: (content, renderer, dom) ->
    super content, renderer, dom

  ###*
    @override
  ###
  decorateChanges: ->
    @grandParent = @dom_.getParentElement @dom_.getParentElement @getElement()
    return unless @grandParent?

    inputs = @dom_.all 'input', @grandParent
    return unless inputs.length?

    @wrappers = @dom.nodeList2Array @dom_.clss(app.ui.changes.AbstractDiscardChanges.CLS.CHANGED_VALUE)

    @fields.push f for f in inputs when f.type isnt 'hidden'
    @toDisappear = @getElement()

  ###*
    @override
  ###
  handleAction: ->
    check = @dom_.cls app.ui.changes.AbstractDiscardChanges.CLS.CHECK, @parent
    check.value = 'on' if check?
    super()
