class app.ui.changes.DiscardChanges extends app.ui.changes.AbstractDiscardChanges

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

    form = @dom_.getAncestorByTagNameAndClass @getElement(), 'form'
    return unless form?

    fieldName = String(goog.dom.dataset.get(@getElement(), app.ui.changes.AbstractDiscardChanges.DATA.FOR))
    @origValEl = @dom_.getElement 'orig_' + fieldName

    @fields = form[fieldName]
    unless @fields.length?
      @fields = [@fields]

    @parent = @dom_.getParentElement @getElement()
    @grandParent = @dom_.getParentElement @parent

    field = @fields[0]
    if @origValEl? and field?
      type = field.type.toLowerCase()
      @val = switch type
        when 'select-multiple' then @getOrigValues()
        else @getOrigValueForInput()

    for f in @fields
      if field.value is @val
        @fields = [f]
        break

    @toDisappear = @parent
