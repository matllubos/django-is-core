class app.ui.zippy.FieldZippy extends wzk.ui.Component

  ###*
    @enum {string}
  ###
  @CONSTANTS:
    HEAD_SELECTOR:  'label'
    BODY_CLASS:  'field-value'
    PREVIEW_TAG:  'div'
    PREVIEW_CLASS:  'preview'
  
  ###*
    @type {number}
  ###
  @PREVIEW_LENGTH: 80

  ###*
    Wrapps given field in zippy

    Use pseudoelement ::after to render arrow representing toggle state, using
    CSS class goog-zippy-expanded

    @param {Object} params
      dom: {@link wzk.dom.Dom}
      renderer: a renderer for the component, defaults {@link wzk.ui.ComponentRenderer}
      caption: {string}
      expanded: {boolean}
  ###
  constructor: (params = {}) ->
    params.expanded ?= false
    super(params)
    {@expanded} = params

  ###*
    @override
  ###
  decorateInternal: (element) ->
    @C = app.ui.zippy.FieldZippy.CONSTANTS

    @head = @dom.one @C.HEAD_SELECTOR, element
    @body = @dom.cls @C.BODY_CLASS, element

    unless @dom.one('p', @body)
      return

    @insertPreview()

    @zippy = new goog.ui.Zippy @head, @body, @expanded
    @zippy.listen goog.ui.Zippy.Events.TOGGLE, @toggle
    undefined

  ###*
    @protected
  ###
  insertPreview: ->
    @preview = @dom.createElement @C.PREVIEW_TAG, @C.PREVIEW_CLASS
    @preview.innerHTML = goog.string.truncate @dom.getTextContent(@body), app.ui.zippy.FieldZippy.PREVIEW_LENGTH
    @dom.insertChildAt @dom.getParentElement(@head), @preview, 1

    goog.events.listen @preview, goog.events.EventType.CLICK, @previewClick

  ###*
    @protected
  ###
  previewClick: =>
    @zippy.expand()

  ###*
    @protected
    @param {goog.events.Event} event
  ###
  toggle: (event) =>
    goog.style.setElementShown @preview, not event.expanded
