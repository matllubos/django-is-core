goog.require 'goog.dom.dataset'
goog.require 'goog.ui.TableSorter'
goog.require 'wzk.ui.ac'
goog.require 'wzk.ui.form.Select'
goog.require 'app.ui.report.CurrencyFormatter'

###*
  Allows to filter by one column specified in data attribute FILTER_NAME
  Is sorted by one column specified in data attribute SORT_NAME
  Sums columns into sum cell in tfoot that had id in form: sum-model-name-of-field (first two can be anything)
  Sum respects filtering
  You can specify currency by CURRENCY data attribute
###
class app.ui.grid.ReportGrid extends wzk.ui.grid.Grid

  ###*
    @enum {string}
  ###
  @DATA:
    CURRENCY: 'currency'
    SORT_NAME: 'sortName'
    FILTER_NAME: 'filterName'

  ###*
    @param {wzk.dom.Dom} dom
    @param {wzk.ui.grid.Repository} repo
    @param {Array.<string>} cols
    @param {wzk.ui.dialog.ConfirmDialog} confirm
    @param {wzk.resource.Query} query
    @param {wzk.ui.grid.Paginator} paginator
  ###
  constructor: (@dom, @repo, @cols, @confirm, @query, @paginator) ->
    super(@dom, @repo, @cols, @confirm, @query, @paginator)
    @data = []

  ###*
    @override
  ###
  decorate: (table) ->
    super(table)
    currency = goog.dom.dataset.get table, 'currency'
    currency ?= ''
    @formatter = new app.ui.report.CurrencyFormatter(currency)

    @sortName = goog.dom.dataset.get table, 'sortName'
    @filterColumn = goog.dom.dataset.get table, 'filterName'
    @sums = @dom.all 'tfoot td[id]', table

  ###*
    @override
  ###
  handleData: (data, result) ->
    unless @select?
      @data = data
      if @filterColumn?
        @buildFilter(data)

    if @filterColumn?
      data = @filter(data, @filterColumn)

    if @sortName?
      data = @sort(data, @sortName)

    super(data, result)
    @sumColumns(data)

  ###*
    @param {Array.<Object>} data
    @param {string} filterColumn
  ###
  filter: (data, filterColumn) ->
    val = goog.dom.forms.getValue @select
    unless val
      return data

    filteredData = []
    for model in data
      if model[@filterColumn]["_raw"] is val
        filteredData.push model

    filteredData

  ###*
    @param {Array.<Object>} data
    @param {string} sortName
  ###
  sort: (data, sortName) ->
    data.sort (a, b) ->
      dateA = new Date(Date.parse(a[sortName]["_raw"])).getTime()
      dateB = new Date(Date.parse(b[sortName]["_raw"])).getTime()
      return dateA - dateB
    data

  ###*
    @protected
    @param {Array.<Object>} data
  ###
  sumColumns: (data) ->
    for sumField in @sums
      idSplits = sumField.getAttribute('id').split('-')
      id = ''
      # first two are "sum" and "name of model", thus ignored
      for idx in [2..idSplits.length - 1]
        id += idSplits[idx]
        if idx < idSplits.length - 1
          id += '_'

      sum = @sumColumn data, id
      sumField.innerHTML = @formatter.format sum

  ###*
    @protected
    @param {Array.<Object>} data
    @param {string} name
  ###
  sumColumn: (data, name) ->
    sum = 0
    for model in data
      if model[name]?["_raw"]?
        sum += parseFloat model[name]["_raw"]
    sum

  ###*
    @protected
    @param {Array.<Object>} data
  ###
  buildFilter: (data) ->
    options = {'': '---'}
    for model in data
      unless options[model[@filterColumn]["_raw"]]
        options[model[@filterColumn]["_raw"]] = model[@filterColumn]["_verbose"]

    select = new wzk.ui.form.Select {options: options}
    select.render @dom.cls(@filterColumn, @table)
    @select = (`/** @type {HTMLSelectElement} */`) select.getElement()

    wzk.ui.ac.buildSelectAutoCompleteNative(@select, @dom)
    goog.events.listen @select, goog.events.EventType.CHANGE, @handleFilter

  ###*
    @protected
    @param {goog.events.Event} event
  ###
  handleFilter: (event) =>
    @handleData(@data, {})
