goog.require 'goog.dom.dataset'

class app.ui.tab.TabBar extends wzk.ui.tab.TabBar

  ###*
    display type that will be setted on selection
    @const
    @type {string}
  ###
  @DISPLAY_TYPE: 'block'

  ###*
    @enum {string}
  ###
  @ORIENTATION:
    HORIZONTAL: 'top',
    VERTICAL: 'start'

  ###*
    @param {wzk.dom.Dom} dom
    @param {string} orientation
  ###
  constructor: (@dom, @orientation) ->
    super undefined, undefined, @dom
    @listen goog.ui.Component.EventType.SELECT, @handleSelect

  ###*
    @override
  ###
  decorate: (el) ->
    # add required goog classes to decorated container
    goog.dom.classes.add el, 'goog-tab-bar', "goog-tab-bar-#{@orientation}"
    @showImplicitlySelected el
    super(el)

  ###*
    @protected
    @param {Element} decoratedElement
  ###
  showImplicitlySelected: (decoratedElement) ->
    # show implicitly selected tab
    for listElement in @dom.getChildren decoratedElement
      # add required goog class to children of decorated container
      goog.dom.classes.add listElement, 'goog-tab'

      input = @dom.one 'input', listElement
      if goog.dom.forms.getValue input
        @select listElement

  ###*
    @protected
    @param {goog.events.Event} event
  ###
  handleSelect: (event) ->
    @select event.target.getElement()

  ###*
    @param {Element} listElement
  ###
  select: (listElement) ->
    selectedInput = @dom.one 'input', listElement
    selectedTab = @getTabFromListElement listElement

    if selectedTab?
      goog.dom.forms.setValue selectedInput, true
      @showTab(selectedTab)
    else
      throw new Error("Given tab does not exist!")

  ###*
    @protected
    @param {Element} listElement
  ###
  getTabFromListElement: (listElement) ->
    # read data attibute denoting element to be shown
    tabId = goog.dom.dataset.get listElement, 'choice'
    selectedTab = @dom.getElement tabId
    selectedTab

  ###*
    Shows only the tab element, hides all his siblings
    @protected
    @param {Element} tab
  ###
  showTab: (tab) ->
    @hideAllSiblings tab
    goog.style.setElementShown tab, true

  ###*
    @protected
    @param {Element} tab
  ###
  hideAllSiblings: (tab) ->
    parentContainer = @dom.getParentElement tab
    tabSiblings = @dom.getChildren parentContainer
    goog.style.setElementShown(tab, false) for tab in tabSiblings