got = require 'got'
{URL} = require 'url'
cheerio = require 'cheerio'
db = require './db.ls'

require! request


HOST = 'sdarot.pm'
IPADDR = '149.202.200.130'

PAGE_URL = new URL("https://#{IPADDR}/watch/")

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36"

DEFAULT_HEADERS =
    'Host': HOST
    'User-Agent': USER_AGENT
    'Content-Type': 'text/html; charset=UTF-8'


fetch-series-page = (series-no) ->
  new Promise (resolve, reject) ->
    request do ->
      uri: new URL(series-no, PAGE_URL)
      headers: DEFAULT_HEADERS
      strictSSL: false
    , (error, response, body) ->
      if error? then reject error
      else resolve {body}


list-episodes = (series-no) ->
  fetch-series-page series-no
  .then ->
    $ = cheerio.load it.body
    episodes = []
      $('li[data-episode]').each (i, e) ->
          ..push $(e).text!trim!
    console.log "  #{episodes.map((.padStart(3, ' '))).join(" ")}"

    # highlight last watched
    data = db.get-series-data series-no
    if (lw = data?last-watched)?
      console.log "#{"    " * lw.episode}*"



if module.id == '.'
  args = process.argv[3 to]

  series-name = args[0]

  if !series-name
    console.error "usage: list_episodes [series]"
  else
    series-no = db.get-series-id-from-name series-name
    list-episodes series-no
