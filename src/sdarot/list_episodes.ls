got = require 'got'
{URL} = require 'url'
cheerio = require 'cheerio'
db = require './db.ls'



PAGE_URL = new URL('http://www.zira.online/watch')

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36"

DEFAULT_HEADERS =
    'User-Agent': USER_AGENT
    'Content-Type': 'text/html; charset=UTF-8'


fetch-series-page = (series-no) ->
  got do
    host: PAGE_URL.hostname
    path: PAGE_URL.pathname + "/#{series-no}"
    headers: {} <<< DEFAULT_HEADERS
    method: 'GET'


list-episodes = (series-no) ->
  fetch-series-page series-no .then ->
      $ = cheerio.load it.body
      $('li[data-episode]').each (i, e) ->
          console.log $(e).text()


if module.id == '.'
  series-no = db.get-series-id-from-name 'spectrum'
  list-episodes series-no
