goog.provide 'app.ui.inlineform'

goog.require 'app'
goog.require 'wzk.ui.inlineform'
goog.require 'goog.dom.dataset'

###*
  @param {Element} el
  @param {wzk.dom.Dom} dom
###
app.ui.inlineform.copy = (el, dom) ->
  goog.events.listen el, 'click', ->
    inputs = [[], []]

    for inline, i in ['source', 'target']
      for input in dom.all(String(goog.dom.dataset.get el, inline) + ' tbody tr input')
        continue if input.type is 'hidden'
        inputs[i].push input

    for source, i in inputs[0]
      inputs[1][i].value = source.value

app._app.on 'fieldset.inline', (el, dom) ->
  wzk.ui.inlineform.buildDynamicButton el, dom

app._app.on '.copy-inline', (el, dom) ->
  app.ui.inlineform.copy el, dom
