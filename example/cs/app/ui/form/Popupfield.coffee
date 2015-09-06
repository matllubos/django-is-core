goog.require 'goog.events'
goog.require 'goog.ui.Dialog'

goog.require 'wzk.ui.dialog.Dialog'
goog.require 'wzk.ui.form.PreventerMultiSubmission'


class app.ui.form.PopupField

  ###*
    @param {wzk.dom.Dom} dom
    @param {Array.<Array.<Element, number>>} triggerOnSelects
    @param {string} triggerValue
  ###
  constructor: (@dom, @triggerOnSelects, @triggerValue) ->
    @origValues = (goog.dom.forms.getValue(tuple[0]) for tuple in @triggerOnSelects)

  ###*
    @param {Element} parent
  ###
  decorate: (parent) ->
    @field = @dom.one('input', parent)

    throw Error('Missing field for a parent element') if not @field??

    @hidden = @dom.el('input', {type: 'hidden', name: @field.name, value: @field.value})
    @dom.insertSiblingAfter(@hidden, parent)
    @dialog = new wzk.ui.dialog.Dialog undefined, undefined, @dom
    @dialog.getButtonSet().clear()
    @dialog.getButtonSet().set(goog.ui.Dialog.DefaultButtonKeys.OK, 'OK', true)
    goog.events.listen(@field.form, 'submit', @handleSubmit)
    goog.events.listen(@dialog, goog.ui.Dialog.EventType.SELECT, @handleOK)
    goog.events.listen(@dialog, goog.ui.Dialog.EventType.AFTER_HIDE, @handleAfterHide)
    @dom.appendChild(@dialog.getContentElement(), parent)

  ###*
    @protected
    @param {goog.events.Event} e
  ###
  handleSubmit: (e) =>
    sum = 0
    showPopup = false
    for tuple, i in @triggerOnSelects
      val = goog.dom.forms.getValue(tuple[0])
      if val is @triggerValue
        if val isnt @origValues[i]
          showPopup = true
        sum += tuple[1]

    if showPopup and @existsAnyFinanceFlowFromEshop()
      e.preventDefault()
      goog.dom.forms.setValue(@field, sum)
      @dialog.open()

  ###*
    @protected
    @param {goog.events.Event} e
  ###
  handleOK: (e) =>
    if e.key is goog.ui.Dialog.DefaultButtonKeys.OK
      goog.dom.forms.setValue(@hidden, goog.dom.forms.getValue(@field))
      @hidden.form.submit()

  ###*
    @protected
    @param {goog.events.Event} e
  ###
  handleAfterHide: (e) =>
    wzk.ui.form.PreventerMultiSubmission.enableButtonsInForm @hidden.form

  ###*
    @protected
    @return {boolean}
  ###
  existsAnyFinanceFlowFromEshop: =>
    for opt in @dom.all('.orderpaymentinlineview select option[selected][value="2"]', @hidden.form)
      row = @dom.getParentElement(@dom.getParentElement(@dom.getParentElement(opt)))
      checkbox = @dom.one('input[type=checkbox]', @dom.getLastElementChild(row))
      if checkbox? and not checkbox.checked
        return true
    return false
