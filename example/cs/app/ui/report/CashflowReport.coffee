goog.require 'app.ui.chart.BarChart'
goog.require 'goog.string'

class app.ui.report.CashflowReport extends app.ui.report.AbstractReport

  ###*
    @param {wzk.resource.Client} client
    @param {Object} d3
  ###
  constructor: (client, d3) ->
    super client, d3

  ###*
    @override
  ###
  render: (el) ->
    super el

  ###*
    @protected
    @return {app.ui.chart.BarChart}
  ###
  buildChart: ->
    new app.ui.chart.BarChart @d3, @size, @formatter

  ###*
    @override
  ###
  handleSuccess: (data) =>
    data = ({'title': @formatDate(o['title']), 'verbose_date': o['title'], 'value': parseFloat(o['value'])} for o in data)
    expert = @buildDataExpert data
    @chart = @buildChart()
    @chart.setExpert expert
    @chart.render @el

  ###*
    @protected
    @param {string} date
    @return {string}
  ###
  formatDate: (date) ->
    if goog.string.countOf(date, '.') is 1
      date = '1.' + date
    tokens = date.split '.'
    [tokens[0], tokens[1], ''].join '.'
