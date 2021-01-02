{URL} = require 'url'
cheerio = require 'cheerio'
db = require './db.ls'

require! request


HOST = 'sdarot.tv'
IPADDR = '149.202.200.130'

WATCH_URL = new URL("https://#{IPADDR}/watch/")
AJAX_URL = new URL("https://#{IPADDR}/ajax/")

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36"

DEFAULT_HEADERS =
  'Host': HOST
  'User-Agent': USER_AGENT
  'Content-Type': 'text/html; charset=UTF-8'
  'referer': 'https://sdarot.tv/'


fetch-series-page = (series-no, season=1) ->
  new Promise (resolve, reject) ->
    request do ->
      uri: new URL("#{series-no}/season/#{season}", WATCH_URL)
      headers: DEFAULT_HEADERS
      strictSSL: false
    , (error, response, body) ->
      if response.headers['set-cookie'] then cookie that.0
      if error? then reject error
      else resolve {body}


list-episodes = (series-no, season=1) ->
  fetch-series-page series-no, season
  .then ->
    $ = cheerio.load it.body
    episodes = []
      $('li[data-episode]').each (i, e) ->
          ..push $(e).text!trim!
    console.log "  #{episodes.map((.padStart(3, ' '))).join(" ")}"

    # highlight last watched
    data = db.get-series-data series-no
    if (lw = data?last-watched)? && season ~= lw?season
      console.log "#{"    " * lw.episode}*"

search = (query) ->
  encoded-query = encodeURIComponent(query)

  new Promise (resolve, reject) ->
    request do ->
      uri: new URL("index?search=#{encoded-query}", AJAX_URL)
      headers: DEFAULT_HEADERS
      strictSSL: false
    , (error, response, body) ->
      console.log response.headers, body
      #console.log JSON.parse(body)
      if response.headers['set-cookie'] then cookie that.0
      if error? then reject error
      else resolve {body}

#https://zira.online/

cookie = (value) ->
  value = value.split(';').0
  db.set-cookie value
  db.write!


if module.id == '.'
  require! commander
  opts = commander
    ..usage '<programme> [options]'
    ..option '-s, --season [num]'  'season number'
    ..option '-e, --episode [num]' 'episode number (set last watched)'
    ..option '-q, --search' 'search for programme'
    .parse process.argv[1 to]

  series-name = opts.args[0]

  if !series-name
    opts.outputHelp!
  else if opts.search
    search series-name
  else
    series-no = db.get-series-id-from-name series-name
    series-data = db.get-series-data(series-no) ? {}
    season = opts.season ? series-data.last-watched?season

    if opts.episode?
      episode = +opts.episode
      db.set-last-watched series-no, {season, episode}
      db.write!

    list-episodes series-no, season

