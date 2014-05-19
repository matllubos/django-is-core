goog.provide 'app.ui.zippy'

goog.require 'wzk.ui.zippy'
goog.require 'app.ui.zippy.FieldZippy'

app._app.on '.messages', (element, dom) ->
  wzk.ui.zippy.buildZippy(element, dom)

app._app.on '.field.description', (element, dom) ->
  fz = new app.ui.zippy.FieldZippy(dom)
  fz.decorate(element)

app._app.on 'ul.collapsable, ol.collapsable', (element, dom) ->
  wzk.ui.zippy.buildCollapsableList element, dom
