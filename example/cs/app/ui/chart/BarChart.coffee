class app.ui.chart.BarChart

  ###*
    @enum {string}
  ###
  @CLS:
    BAR: 'bar'
    X_AXIS: 'x axis'
    Y_AXIS: 'y axis'

  ###*
    @enum {number}
  ###
  @SIZE:
    WIDTH: 960
    HEIGHT: 500

  ###*
    @param {Object} d3
    @param {Object} size
    @param {app.ui.report.Formatter} formatter
  ###
  constructor: (@d3, size, @formatter) ->
    @margin = {top: 20, right: 20, bottom: 30, left: 40}
    {@width, @height} = size
    @width ?= app.ui.chart.BarChart.SIZE.WIDTH
    @height ?= app.ui.chart.BarChart.SIZE.HEIGHT
    @width = @width - @margin.left - @margin.right
    @height = @height - @margin.top - @margin.bottom
    @y = null
    @x = null
    @svg = {}
    @tip = null
    @expert = null
    @g = {}

  ###*
    @param {app.ui.chart.DataExpert} expert
  ###
  setExpert: (@expert) ->

  ###*
    @param {Element} el
  ###
  render: (el) ->
    @x = @d3['scale']['ordinal']()['rangeRoundBands']([0, @width], .1)
    @y = @d3['scale']['linear']()['range']([@height, 0])

    @buildXAxis()
    @buildYAxis()
    @buildTip()
    @buildSvg el

    @x['domain'](@expert.map((d) => @expert.getLabel(d)))
    @y['domain']([0, @d3.max(@expert.getData(), (d) => @expert.getValue(d))])

    @formatXAxis()
    @formatYAxis()
    @formatBar()

    @g['transition']().duration(400)['style'] 'opacity', 1

  ###*
    @protected
  ###
  buildTip: ->
    @tip = @d3['tip']()['attr']('class', 'd3-tip')['offset']([-10, 0])['html'](@getTipHtml)

  ###*
    @protected
    @param {Object} d
  ###
  getTipHtml: (d) =>
    ['<span class="tooltip-date">', d['verbose_date'], '</span>&nbsp;-&nbsp;', @formatter.format(@expert.getValue(d))].join ''

  ###*
    @protected
  ###
  formatBar: ->
    CLS = app.ui.chart.BarChart.CLS.BAR
    rect = @svg['selectAll']("." + CLS)['data'](@expert.getData())['enter']()['append']("rect")
    rect['attr']("class", CLS)
    rect['attr']("x", (d) => @x(@expert.getLabel(d)))
    rect['attr']("width", @x['rangeBand']())
    rect['attr']("y", (d) => @y(@expert.getValue(d)))
    rect['attr']("height", (d) => @height - @y(@expert.getValue(d)))
    rect['on']('mouseover', @tip['show'])
    rect['on']('mouseout', @tip['hide'])

  ###*
    @protected
    @param {Element} el
  ###
  buildSvg: (el) ->
    @g = @d3.select(el).append("svg")
    @g['style'] 'opacity', 0
    @g['attr']("width", @width + @margin.left + @margin.right)
    @g['attr']("height", @height + @margin.top + @margin.bottom)
    @svg = @g['append']("g")
    @svg['attr']("transform", ["translate(", @margin.left, ",", @margin.top, ")"].join(''))
    @svg.call @tip

  ###*
    @protected
  ###
  buildXAxis: ->
    @xAxis = @d3['svg']['axis']()['scale'](@x)['orient']("bottom")

  ###*
    @protected
  ###
  buildYAxis: ->
    @yAxis = @d3['svg']['axis']()['scale'](@y)['orient']("left")['tickFormat']((d) -> String(d / 1000) + "k")

  ###*
    @protected
  ###
  formatXAxis: ->
    g = @svg['append']("g")['attr']("class", app.ui.chart.BarChart.CLS.X_AXIS)
    g['attr']("transform", "translate(0," + @height + ")")['call'](@xAxis)

  ###*
    @protected
  ###
  formatYAxis: ->
    t = @svg['append']("g")['attr']("class", app.ui.chart.BarChart.CLS.Y_AXIS)['call'](@yAxis)['append']("text")
    t['attr']("transform", "rotate(-90)")
    t['attr']("y", 6)
    t['attr']("dy", ".71em")
    t['style']("text-anchor", "end")
