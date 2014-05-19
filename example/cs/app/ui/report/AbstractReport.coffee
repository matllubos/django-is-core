goog.require 'goog.dom.dataset'
goog.require 'app.ui.chart.DataExpert'
goog.require 'wzk.num'
goog.require 'app.ui.report.CurrencyFormatter'

class app.ui.report.AbstractReport

  ###*
    @enum {Function}
  ###
  @DATA:
    'height': wzk.num.parseDec
    'width': wzk.num.parseDec

  ###*
    @param {wzk.resource.Client} client
  ###
  constructor: (@client, @d3) ->
    @el = null
    @formatter = null

  ###*
    @protected
    @param {Array} data
    @return {app.ui.chart.DataExpert}
  ###
  buildDataExpert: (data = []) ->
    new app.ui.chart.DataExpert data

  ###*
    @protected
    @param {string} name
    @param {*=} implicit
    @return {*}
  ###
  data: (name, implicit) ->
    return undefined unless @el
    val = String goog.dom.dataset.get(@el, name)
    if app.ui.report.AbstractReport.DATA[name]
      val = app.ui.report.AbstractReport.DATA[name] val, implicit
    val

  ###*
    @param {Element} el
  ###
  render: (@el) ->
    @formatter = new app.ui.report.CurrencyFormatter String @data 'currency'
    @size =
      width: @data 'width', app.ui.chart.BarChart.SIZE.WIDTH
      height: @data 'height', app.ui.chart.BarChart.SIZE.HEIGHT

    @loadData()

  ###*
    @protected
  ###
  loadData: ->
    @client.find String(@data('url')), @handleSuccess

  ###*
    @protected
    @param {Array} data
    @return {*}
  ###
  handleSuccess: (data) ->

  ###*
    Renders collapsable list using app.ui.report.DataList
    @protected
    @param {Array.<Object>} data
  ###
  renderData: (data) ->
    dataList = new app.ui.report.DataList(data, @formatter, {dom: @dom})
    dataList.render @el
