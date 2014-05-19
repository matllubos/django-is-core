class app.ui.grid.ToggleFilter extends wzk.ui.Component

  ###*
    @enum {string}
  ###
  @CLASSES:
    FILTER_CLASS: 'filter-wrapper'
    ACTIVE_CLASS: 'active'
    HIDDEN_CLASS: 'hidden-transition'
    SHOWN_CLASS: 'filter-shown'
    CLEAR_FILTER_BUTTON: 'clear-filter'

  ###*
    @param {Object} params
      dom: {@link wzk.dom.Dom}
      renderer: a renderer for the component, defaults {@link wzk.ui.ComponentRenderer}
      caption: {string}
  ###
  constructor: (params = {}) ->
    super params
    @C = app.ui.grid.ToggleFilter.CLASSES
    @elements = []

  ###*
    @override
  ###
  decorateInternal: (element) ->
    @setElementInternal element
    @elements = @findElements(element)
    @setVisibleAll @elements, false

    goog.events.listen element, goog.events.EventType.CLICK, @toggleFilter
    undefined

  ###*
    @protected
    @param {Element} el
  ###
  findElements: (el) ->
    tr = @dom.getParentElement @dom.getParentElement @dom.getParentElement el
    filterInputs = @dom.clss @C.FILTER_CLASS, tr
    filterInputs = @dom.nodeList2Array filterInputs

    @clearButton = @dom.cls @C.CLEAR_FILTER_BUTTON, tr
    goog.events.listen @clearButton, goog.events.EventType.CLICK, @clear

    filterInputs.push @clearButton
    filterInputs

  ###*
    @protected
  ###
  toggleFilter: =>
    if goog.dom.classes.has @getElement(), @C.ACTIVE_CLASS
      @setVisibleAll @elements, false
      goog.dom.classes.remove @getElement(), @C.ACTIVE_CLASS
    else
      @setVisibleAll @elements, true
      goog.dom.classes.add @getElement(), @C.ACTIVE_CLASS

  ###*
    @protected
  ###
  clear: =>
    for el in @elements
      el = @dom.one 'input, select', el

      if el?
        if el instanceof HTMLSelectElement
          val = el.querySelector('option').value
          goog.dom.forms.setValue el, val
        else
          goog.dom.forms.setValue el, ''
        goog.events.fireListeners(el, goog.events.EventType.KEYUP, false, {type: goog.events.EventType.KEYUP, target:el})

  ###*
    @protected
    @param {(Array.<?>|NodeList)} elements to hide
    @param {boolean} visibility
  ###
  setVisibleAll: (elements, visibility) ->
    for el in elements
      if visibility
        goog.dom.classes.remove el, @C.HIDDEN_CLASS
        goog.dom.classes.add el, @C.SHOWN_CLASS
      else
        goog.dom.classes.add el, @C.HIDDEN_CLASS
        goog.dom.classes.remove el, @C.SHOWN_CLASS
