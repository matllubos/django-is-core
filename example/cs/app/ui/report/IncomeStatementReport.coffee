goog.require 'app.ui.chart.PieChart'
goog.require 'app.ui.report.DataList'

class app.ui.report.IncomeStatementReport extends app.ui.report.AbstractReport

  ###*
    @enum {string}
  ###
  @CLS:
    REVENUES: 'chart-revenues'
    COSTS: 'chart-costs'

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
    formatted = []
    for piece in data
      continue unless piece['subrows']
      formatted.push @preparePieceData piece['subrows']

    CLS = app.ui.report.IncomeStatementReport.CLS
    for klass, i in [CLS.REVENUES, CLS.COSTS]
      expert = new app.ui.chart.DataExpert formatted[i]

      params = @size
      params.formatter = @formatter
      chart = new app.ui.chart.PieChart @d3, expert, params
      chart.decorate @el.querySelector('.' + klass)

    @renderData data

  ###*
    @protected
    @param {Object} piece
    @return {Object}
  ###
  preparePieceData: (piece) ->
    sum = 0
    data = []
    for item in piece
      parsed = {}
      parsed['value'] = parseFloat item['value']
      parsed['label'] = item['title']
      sum += parsed['value']
      data.push parsed

    return data if sum is 0
    data
