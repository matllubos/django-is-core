goog.provide 'app.ui.form'

goog.require 'goog.events'
goog.require 'goog.dom'
goog.require 'goog.array'

goog.require 'wzk.ui.form.PreventerMultiSubmission'

goog.require 'app.ui.form.ForwardEnterSubmit'
goog.require 'app.ui.form.PopupField'


app._app.on '.member-registration-form', (el, dom) ->
  forwarder = new app.ui.form.ForwardEnterSubmit dom
  forwarder.forward el, dom.cls('send-verification-sms-btn', el)

app._app.on '.click-once-btn', (el, dom) ->
  goog.events.listen el, goog.events.EventType.CLICK, ->
    dom.hide el

app._app.on '.app-backend form', (el, dom) ->
  preventer = new wzk.ui.form.PreventerMultiSubmission dom
  preventer.prevent el

app._app.on '.gate-form input, .gate-form button', (el, dom) ->
  dom.setProperties el, tabIndex: 1

app._app.on '.modal-form', (el, dom, xhrFac, opts) ->
  wzk.ui.form.buildModalForm el, dom, xhrFac, opts.app.getRegister()

app._app.on '.field.issued_eshop_credit_note', (el, dom) ->
  values = dom.all('.inline.orderitem .inline-line .field:nth-child(3) p')
  triggerOnSelects = goog.array.zip(
    goog.array.map(dom.all('.inline.orderitem select[name$=state]'), (obj) -> obj),
    goog.array.map(values, (element) -> parseFloat(element.innerHTML.replace(',', '.')))
  )
  popupField = new app.ui.form.PopupField(dom, triggerOnSelects, '2')
  popupField.decorate(el)
