goog.require 'app.ui.report.DataList'

class app.ui.report.DataRowsReport extends app.ui.report.AbstractReport

  ###*
    @param {wzk.resource.Client} client
  ###
  constructor: (@client, @d3) ->
    super(@client, @d3)

  ###*
    @override
  ###
  handleSuccess: (data) =>
    @renderData data
