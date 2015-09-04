goog.require 'goog.dom.classes'

goog.require 'wzk.num'

class app.ui.ScoreStars extends goog.ui.Component

  ###*
    @enum {string} classes
  ###
  @CLS:
    STAR: 'star'
    STARS_WRAP: 'stars-wrap'
    FULL_STAR: 'full-star'

  ###*
    @const {number}
  ###
  @MAX_SCORE: 4

  ###*
    @param {wzk.dom.Dom} dom
  ###
  constructor: (@dom) ->
    @starsNum = 0

  ###*
    @param {Element} el
  ###
  decorate: (@el) ->
    super @el
    @starsNum = wzk.num.parseDec goog.dom.getTextContent(@el)
    @render()

  ###*
    @protected
  ###
  render: ->
    div = @dom.el 'div', app.ui.ScoreStars.CLS.STARS_WRAP
    for i in [0..app.ui.ScoreStars.MAX_SCORE]
      span = @dom.el('span', if i <= @starsNum - 1 then app.ui.ScoreStars.CLS.FULL_STAR else '')
      goog.dom.classes.add span, app.ui.ScoreStars.CLS.STAR
      div.appendChild span

    @el.innerHTML = ''
    @el.appendChild div
