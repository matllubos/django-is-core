class app.ui.report.DataList extends wzk.ui.Component

  ###*
    @enum {string}
  ###
  @CLS:
    COLLAPSABLE: 'collapsable'

  ###*
    @param {Object} data
    @param {app.ui.report.CurrencyFormatter} formatter
    @param {Object} params
      dom: {@link wzk.dom.Dom}
      renderer: a renderer for the component, defaults {@link wzk.ui.ComponentRenderer}
      caption: {string}
  ###
  constructor: (@data, @formatter, params = {}) ->
    super(params)

  ###*
    @override
  ###
  render: (el) ->
    ul = @dom.createDom 'ul', app.ui.report.DataList.CLS.COLLAPSABLE
    for row in @data
      @renderList row, ul
    @dom.appendChild el, ul
    wzk.ui.zippy.buildCollapsableList ul, @dom

  ###*
    @protected
    @param {Object} row
      subrows: {Array.<Object>}
      value: {number}
      title: {string}
    @param {Element} el
  ###
  renderList: (row, el) ->
    li = @dom.createDom 'li'
    cont = @dom.el 'span', 'collapsable-wrapper'
    @dom.el 'span', 'collapsable-icon', cont
    title = @dom.el 'span', 'collapsable-title', cont
    title.innerHTML = "#{row["title"]}"
    title.innerHTML += ": <strong>#{@formatter.format(row["value"])}</strong>" if row['value']?
    @dom.appendChild li, cont

    if row["subrows"]?
      ul = @dom.createDom 'ul', app.ui.report.DataList.CLS.COLLAPSABLE
      for row in row["subrows"]
        @renderList(row, ul)
      @dom.appendChild li, ul
    else
      goog.dom.classes.add cont, 'subvalue'

    @dom.appendChild el, li
