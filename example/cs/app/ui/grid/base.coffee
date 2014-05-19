goog.provide 'app.ui.grid'

goog.require 'app.ui.grid.ToggleFilter'
goog.require 'app.ui.grid.ReportGrid'

###*
  @param {Element} table
  @param {wzk.dom.Dom} dom
  @param {wzk.net.XhrFactory} factory
  @param {wzk.app.Register} reg
  @param {wzk.stor.StateStorage} ss
  @return {wzk.ui.grid.Grid}
  @suppress {checkTypes}
###
app.ui.grid.build = (table, dom, factory, reg, ss) ->
  wzk.ui.grid.buildGrid table, dom, factory, reg, ss, app.ui.grid.ReportGrid

app._app.on '.toggle-filter', (element, dom) ->
  tf = new app.ui.grid.ToggleFilter(dom)
  tf.decorate(element)

app._app.on '.report-grid', (element, dom, factory) ->
  app.ui.grid.build element, dom, factory, app._app.getRegister(), app._app.getStorage('g')
