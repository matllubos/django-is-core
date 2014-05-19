class app.ui.chart.PieChart

  ###*
    @const {number}
  ###
  @WORD_WRAP_LINE_HEIGHT: 0.5

  ###*
    @const {number}
  ###
  @WORD_WRAP_WIDTH: 10

  ###*
    @param {Object} d3
    @param {app.ui.chart.DataExpert} dataExpert
    @param {Object=} params
      width {number}
      height {number}
      colors {Array.<String>}
  ###
  constructor: (@d3, @dataExpert, params = {}) ->
    @["d3"] = @d3
    params = {} unless params?

    @width = params.width or 800
    @height = params.height or 300
    @colors = params.colors or [
      "#98abc5"
      "#8a89a6"
      "#7b6888"
      "#6b486b"
      "#a05d56"
      "#d0743c"
      "#ff8c00"
    ]

    if params.formatter
      @formatter = params.formatter

    # calculated params
    @radius = Math.min(@width, @height) / 2

    # prepare colors
    ordinalScale = @d3["scale"]["ordinal"]()
    @color = ordinalScale["range"] @colors

  ###*
    @param {Element} el
  ###
  decorate: (@el) ->
    d3el = @d3["select"](@el)
    @svgElement = d3el["append"]("svg")
    @svg = @svgElement["append"]("g")

    goog.style.setSize @svgElement[0][0], @width, @height

    d3el['style'] 'opacity', '0'

    @svg["append"]("g")["attr"] "class", "slices"
    @svg["append"]("g")["attr"] "class", "labels"
    @svg["append"]("g")["attr"] "class", "lines"

    @pie = @d3["layout"]["pie"]()["sort"](null)["value"]((d) ->
      d.value
    )

    @arc = @d3["svg"]["arc"]()["outerRadius"](@radius * 0.8)["innerRadius"](@radius * 0.4)
    @outerArc = @d3["svg"]["arc"]()["innerRadius"](@radius * 0.9)["outerRadius"](@radius * 0.9)
    @svg["attr"] "transform", "translate(" + @width / 2 + "," + @height / 2 + ")"

    @formatData()
    @render()
    d3el['transition']().duration(400)['style'] 'opacity', 1

  ###*
    @protected
  ###
  render: ->
    pdata = @pie @dataExpert.getData()

    @buildTip()
    @svg.call @tip

    @buildSlices(pdata)
    @buildTextLabels(pdata)
    @buildLinesToText(pdata)

  ###*
    @protected
  ###
  formatData: ->
    sum = 0
    for item in @dataExpert.getData()
      sum += item['value']

    return if sum is 0

    for item in @dataExpert.getData()
      item['piece'] = item['value'] / sum

  ###*
    @protected
    @param {Object} data
  ###
  buildSlices: (data) ->
    slice = @svg["select"](".slices")["selectAll"]("path.slice")["data"](data, @key)

    i = 0
    slice["enter"]()["insert"]("path")["attr"]("class", ->
      "slice slice-#{++i}"
    )

    that = @
    slice["transition"]()["duration"](1000)["attrTween"] "d", (d) ->
      @_current = @_current or d
      interpolate = that.d3["interpolate"](@_current, d)
      @_current = interpolate(0)
      (t) =>
        that.arc interpolate(t)

    slice['on'] 'mouseover', @tip['show']
    slice['on'] 'mousemove', (d) ->
      bounds = this["getBoundingClientRect"]()

      # move tip to top left corner of slice (tip is in the middle by default)
      e = that["d3"]["event"]
      x = - (bounds["width"] / 2)
      y = 0

      # move tip to mouse position
      x += e["clientX"] - bounds["left"]
      y += e["clientY"] - bounds["top"]

      # move tip slightly to up-left, so that it does not overlap mouse cursor
      x -= 10
      y -= 10

      that.tip["offset"] [y, x]
      that.tip['show'](d)

    slice['on']('mouseout', @tip['hide'])
    slice["exit"]()["remove"]()

  ###*
    @protected
    @param {Object} data
  ###
  buildTextLabels: (data) ->
    that = @
    text = @svg["select"](".labels")["selectAll"]("text")["data"](data, @key)
    text["enter"]()["append"]("text")["attr"]("dy", ".35em")["text"] (d) ->
      d["data"]["label"]

    text["transition"]()["duration"](1000)["attrTween"]("transform", (d) ->
      @_current = @_current or d
      interpolate = that.d3["interpolate"](@_current, d)
      @_current = interpolate(0)
      (t) ->
        d2 = interpolate(t)
        pos = that.outerArc["centroid"](d2)
        pos[0] = that.radius * ((if that.midAngle(d2) < Math.PI then 1 else -1))
        "translate(" + pos + ")"
    )["styleTween"] "text-anchor", (d) =>
      @_current = @_current or d
      interpolate = that.d3["interpolate"](@_current, d)
      @_current = interpolate(0)
      (t) ->
        d2 = interpolate(t)
        (if that.midAngle(d2) < Math.PI then "start" else "end")

    text["exit"]()["remove"]()

  ###*
    @protected
    @param {Object} data
  ###
  buildLinesToText: (data) ->
    that = @
    polyline = @svg["select"](".lines")["selectAll"]("polyline")["data"](data, @key)
    polyline["enter"]()["append"] "polyline"
    polyline["transition"]()["duration"](1000)["attrTween"] "points", (d) ->
      @_current = @_current or d
      interpolate = that.d3["interpolate"](@_current, d)
      @_current = interpolate(0)
      (t) ->
        d2 = interpolate(t)
        pos = that.outerArc["centroid"](d2)
        pos[0] = that.radius * 0.95 * ((if that.midAngle(d2) < Math.PI then 1 else -1))
        [
          that.arc["centroid"](d2)
          that.outerArc["centroid"](d2)
          pos
        ]

    polyline["exit"]()["remove"]()

  ###*
    @protected
  ###
  buildTip: ->
    @tip = @d3['tip']()['attr']('class', 'd3-tip')
    @tip['html'](@getTipHtml)

  ###*
    @protected
    @param {Object} d
    @return {string}
  ###
  getTipHtml: (d) =>
    tokens = ['<span class="piece-pie">', Math.round(d['data']['piece'] * 100), '&nbsp;%</span>&nbsp;-&nbsp;']
    tokens.push if @formatter? then @formatter.format(@dataExpert.getValue(d)) else @dataExpert.getValue(d)
    tokens.join ''

  ###*
    @protected
    @param {Object} d
  ###
  midAngle: (d) ->
    d["startAngle"] + (d["endAngle"] - d["startAngle"]) / 2

  ###*
    @protected
    @param {Object=} d
  ###
  key: (d) ->
    d['data']['label']
