goog.provide 'app.ui.tab'

goog.require 'wzk.ui.tab'
goog.require 'app.ui.tab.TabBar'

app._app.on '.goog-tabs', (el, dom) ->
  wzk.ui.tab.decorate el, dom
