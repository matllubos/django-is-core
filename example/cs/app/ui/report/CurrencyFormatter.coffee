goog.require 'goog.i18n.NumberFormat'

class app.ui.report.CurrencyFormatter extends app.ui.report.Formatter

  ###*
    @param {string=} currency
  ###
  constructor: (@currency = 'CZK') ->
    super()
    @fmt = new goog.i18n.NumberFormat(goog.i18n.NumberFormat.Format.CURRENCY)

  ###*
    @override
  ###
  format: (value) ->
    "<span class=\"value\">#{@czechFormat(String(value))}</span>&nbsp;<span class=\"currency\">#{@currency}</span>"

  ###*
    @protected
    @param {string} value
    @return {string}
  ###
  czechFormat: (value) ->
    val = @fmt.format parseFloat value
    val = val.substring 1, val.length - 3
    val = val.replace /,/g, ' '
    val
