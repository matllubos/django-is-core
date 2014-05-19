goog.provide 'app.ui.richtooltip'

goog.require 'app'
goog.require 'goog.dom.dataset'
goog.require 'goog.ui.Tooltip'

app._app.on '[data-title]', (element) ->
  title = goog.dom.dataset.get element, 'title'
  new goog.ui.Tooltip element, title
