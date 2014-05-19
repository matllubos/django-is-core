goog.provide 'app.ui.report'

goog.require 'app'
goog.require 'app.ui.report.CashflowReport'
goog.require 'app.ui.report.IncomeStatementReport'
goog.require 'app.ui.report.AssetsReport'
goog.require 'app.ui.report.DataRowsReport'
goog.require 'wzk.resource.Client'

app._app.on '.data-rows-report', (el, dom, xhrFac) ->
  widget = new app.ui.report.DataRowsReport new wzk.resource.Client(xhrFac), dom.getWindow()['d3']
  widget.render el

app._app.on '.cashflow-report', (el, dom, xhrFac) ->
  widget = new app.ui.report.CashflowReport new wzk.resource.Client(xhrFac), dom.getWindow()['d3']
  widget.render el

app._app.on '.income-statement-report', (el, dom, xhrFac) ->
  widget = new app.ui.report.IncomeStatementReport new wzk.resource.Client(xhrFac), dom.getWindow()['d3']
  widget.render el

app._app.on '.assets-report', (el, dom, xhrFac) ->
  widget = new app.ui.report.AssetsReport new wzk.resource.Client(xhrFac), dom.getWindow()['d3']
  widget.render el
