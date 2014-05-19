goog.provide 'app.ui.form'

goog.require 'app'
goog.require 'wzk.ui.form'
goog.require 'wzk.ui.ac'
goog.require 'wzk.resource.Client'
goog.require 'wzk.ui.form.AjaxForm'

###*
  @param {Element} el
  @param {wzk.dom.Dom} dom
  @param {wzk.net.XhrFactory} xhrFac
###
app.ui.form.ajaxifyForm = (el, dom, xhrFac) ->
  client = new wzk.resource.Client xhrFac
  form = new wzk.ui.form.AjaxForm client, dom
  form.cleanAfterSubmit true
  form.decorate el

app._app.on '.remote-button', (el, dom, xhrFac) ->
  wzk.ui.form.buildRemoteButton el, dom, xhrFac

app._app.on 'form.ajax', (form, dom, xhrFac) ->
  app.ui.form.ajaxifyForm form, dom, xhrFac

app._app.on '*[data-modal]', (el, dom, xhrFac, opts) ->
  wzk.ui.form.openFormInModal el, dom, xhrFac, opts.app

app._app.on 'select.fulltext-search', (el, dom) ->
  el = (`/** @type {HTMLSelectElement} */`) el
  wzk.ui.ac.buildSelectAutoCompleteNative el, dom
  
app._app.on 'select.fulltext-search-multiple', (el, dom) ->
  el = (`/** @type {HTMLSelectElement} */`) el
  wzk.ui.ac.buildExtSelectboxFromSelectNative el, dom

