###*
  @see http://www.lalit.org/wordpress/wp-content/uploads/2008/05/fontdetect.js?ver=0.3
###
class app.support.FontDetector

  ###*
    We use m or w because these two characters take up the maximum width.
    And we use a LLi so that the same matching fonts can get separated
    @const
  ###
  @TESTING_STRING: 'mmmmmmmmmmlli'

  ###*
    @const
  ###
  @BASE_FONTS: ['monospace', 'sans-serif', 'serif']

  ###*
    @const
  ###
  @FONT_SIZE: '72px'

  ###*
    @param {Document} doc
  ###
  constructor: (@doc) ->

  ###*
    @protected
  ###
  calibrate: ->
    return if @body?

    @body = @doc.body
    @el = @doc.createElement('span')
    @el.style.fontSize = app.support.FontDetector.FONT_SIZE
    @el.innerHTML = app.support.FontDetector.TESTING_STRING
    @defaultWidth = {}
    @defaultHeight = {}
    for font in app.support.FontDetector.BASE_FONTS
      # get the default width for the three base fonts
      @el.style.fontFamily = font
      @body.appendChild(@el)
      @defaultWidth[font] = @el.offsetWidth # width for the default font
      @defaultHeight[font] = @el.offsetHeight # height for the defualt font
      @body.removeChild(@el)

  ###*
    Returns true if a browser supports a given font, otherwise false.

    @param {string} font
    @return {boolean}
  ###
  detect: (font) ->
    @calibrate()

    detected = false
    for baseFont in app.support.FontDetector.BASE_FONTS
      @el.style.fontFamily = font + ',' + baseFont # name of the font along with the base font for fallback.
      @body.appendChild(@el)
      matched = (@el.offsetWidth isnt @defaultWidth[baseFont] or @el.offsetHeight isnt @defaultHeight[baseFont])
      @body.removeChild(@el)
      detected = detected or matched
    detected
