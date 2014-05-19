goog.require 'app.ui.chart.DataExpert'
goog.require 'app.ui.chart.PieChart'

class app.ui.report.AssetsReport extends app.ui.report.AbstractReport

  ###*
    @const {string} chart selector
  ###
  @CHART_SELECT: '.assets-chart'

  ###*
    @param {wzk.resource.Client} client
    @param {Object} d3
  ###
  constructor: (client, @d3) ->
    super client, @d3

  ###*
    @override
  ###
  handleSuccess: (data) =>
    pieces = @aggregateData data

    expert = new app.ui.chart.DataExpert pieces
    params = @size
    params.formatter = @formatter
    chart = new app.ui.chart.PieChart @d3, expert, params
    chart.decorate @el.querySelector app.ui.report.AssetsReport.CHART_SELECT

  ###*
    @protected
    @param {Object} data
  ###
  aggregateData: (data) ->
    aggregation = {}
    @translations = {}
    for row in data
      type = row["type_name"]["_raw"]
      price = row["price"]["_raw"]
      @translations[type] = row["type_name"]["_verbose"]

      unless aggregation[type]?
        aggregation[type] = 0
      aggregation[type] += parseFloat price

    @prepareData aggregation

  ###*
    @protected
    @param {Object} aggregation
  ###
  prepareData: (aggregation) ->
    pieces = []
    for key, value of aggregation
      piece = {}
      piece["value"] = value
      piece["label"] = @translations[key]
      pieces.push piece
    pieces
