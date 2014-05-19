class app.ui.chart.DataExpert

  ###*
    @param {Array.<Object>} data
  ###
  constructor: (@data) ->
    @labelGetter = (item) ->
      item['title']
    @valueGetter = (item) ->
      item['value']

  ###*
    @param {Array.<Object>} data
  ###
  setData: (@data) ->

  ###*
    @return {Array.<Object>}
  ###
  getData: ->
    @data

  ###*
    @param {function(Object)} labelGetter
  ###
  setLabelGetter: (@labelGetter) ->

  ###*
    @param {function(Object)} valueGetter
  ###
  setValueGetter: (@valueGetter) ->

  ###*
    @param {Object} item
    @return {*}
  ###
  getLabel: (item) ->
    @labelGetter item

  ###*
    @param {Object} item
    @return {*}
  ###
  getValue: (item) ->
    @valueGetter item

  ###*
    @param {function(Object):*} clbk
    @return {Array.<*>}
  ###
  map: (clbk) ->
    (clbk item for item in @data)
