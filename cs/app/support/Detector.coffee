class app.support.Detector

  ###*
    @const
  ###
  @FONTS: [
    "cursive", "monospace", "serif", "sans-serif", "fantasy", "default", "Arial", "Arial Black", "Arial Narrow",
    "Arial Rounded MT Bold", "Bookman Old Style", "Bradley Hand ITC", "Century", "Century Gothic", "Comic Sans MS",
    "Courier", "Courier New", "Georgia", "Gentium", "Impact", "King", "Lucida Console", "Lalit", "Modena",
    "Monotype Corsiva", "Papyrus", "Tahoma", "TeX", "Times", "Times New Roman", "Trebuchet MS", "Verdana", "Verona"
  ]

  ###*
    @const
  ###
  @VIDEO_FORMATS:
    'ogg': 'video/ogg; codecs="theora"'
    'h264': 'video/mp4; codecs="avc1.42E01E"'
    'webm': 'video/webm; codecs="vp8, vorbis"'
    'vp9': 'video/webm; codecs="vp9"'
    'hls': 'application/x-mpegURL; codecs="avc1.42E01E"'

  ###*
    @param {Window} win
    @param {fontDetector} app.support.FontDetector
  ###
  constructor: (@win, @fontDetector) ->

  ###*
    @return {boolean}
  ###
  hasDoNotTrack: ->
    @win.navigator['doNotTrack']?

  ###*
    @return {boolean}
  ###
  hasIndexedDB: ->
    @win.indexedDB?

  ###*
    @return {boolean}
  ###
  hasApplicationCache: ->
    @win.applicationCache?

  ###*
    @return {boolean}
  ###
  hasWebWorker: ->
    @win.Worker?

  ###*
    @return {boolean}
  ###
  hasSessionStorage: ->
    @win.sessionStorage?

  ###*
    @return {boolean}
  ###
  hasLocalStorage: ->
    @win.localStorage?

  ###*
    @return {boolean}
  ###
  hasCanvas: ->
    unless @canvas?
      el = @win.document.createElement('canvas')
      @canvas = el.getContext? and el.getContext('2d')?
    @canvas

  ###*
    @return {boolean}
  ###
  hasVideo: ->
    unless @video?
      el = @win.document.createElement('video')
      @video = el?.canPlayType?
    @video

  ###*
    @return {Array.<string>}
  ###
  getSupportedVideoFormats: ->
    unless @supportedVideoFormats?
      @supportedVideoFormats = []
      if @hasVideo()
        el = @win.document.createElement('video')
        for k, v of app.support.Detector.VIDEO_FORMATS
          try
            if el.canPlayType(v) isnt 'no'
              @supportedVideoFormats.push k
          catch e
            # not supported pass silently
    @supportedVideoFormats

  ###*
    @return {Array.<string>}
  ###
  getSupportedFonts: ->
    unless @supportedFonts?
      @supportedFonts = (font for font in app.support.Detector.FONTS when @fontDetector.detect(font))
    @supportedFonts

  ###*
    @return {string|null}
  ###
  getOs: ->
    return @win.navigator['cpuClass'] if @win.navigator['cpuClass']?
    return @win.navigator.oscpu if @win.navigator.oscpu?
    null

  ###*
    @return {string|null}
  ###
  getPlatform: ->
    return null unless @win.navigator.platform?
    @win.navigator.platform

  ###*
    Returns a browser language (cross-browser)

    @return {string}
  ###
  getLang: ->
    return @win.navigator.browserLanguage if @win.navigator.browserLanguage?
    @win.navigator.language

  ###*
    @return {number}
  ###
  getWindowWidth: ->
    @win.innerWidth or @win.document.documentElement.clientWidth or @win.document.body.clientWidth

  ###*
    @return {number}
  ###
  getWindowHeight: ->
    @win.innerHeight or @win.document.documentElement.clientHeight or @win.document.body.clientHeight
