fs = require 'fs'
http = require 'http'
got = require 'got'
dns = require 'dns'
{URL} = require 'url'
RegExp.quote = require 'regexp-quote'
db = require './db.ls'

require! request


HOST = 'sdarot.pm' #zira.online'
IPADDR = '149.202.200.130'

WATCH_URL = new URL("https://#{IPADDR}/ajax/watch")

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36"

COOKIE = '_ga=GA1.2.486464997.1518630789; Sdarot=sTpq211CqWVoLzPxyeU5Lbc358RJutZn48XkNHXwfDY1tUQSmASJrm7OzzoiFhbKlU8Au0Td5sVJhBUyi3DDVl4UE1C9YMJeyUk4UDAhOyxeUuhe7gsZdWKjZsQi0MVr; _gid=GA1.2.1224283793.1527699600; _gat=1'

DEFAULT_HEADERS =
      'Host': HOST
      'User-Agent': USER_AGENT
      'Cookie': COOKIE
      'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
      'Origin': "http://#{WATCH_URL.hostname}"
      'Referer': "http://#{WATCH_URL.hostname}/watch"
#      'X-Requested-With': 'XMLHttpRequest'
#      'Accept': 'application/json, text/javascript, */*; q=0.01'
#      'Connection': 'keep-alive'
#      'Accept-Encoding': 'gzip, deflate'


invoke = (qstring) ->
  headers =
    'Content-Length': Buffer.byteLength(qstring)

  new Promise (resolve, reject) ->
    request do ->
      uri: WATCH_URL
      method: 'POST'
      headers: {} <<< DEFAULT_HEADERS <<< headers
      strictSSL: false
      body: qstring
    , (error, response, body) ->
      if error? then reject error
      else resolve {body}
  /*
  got do
    host: HOST # WATCH_URL.hostname
    path: WATCH_URL.pathname
    protocol: WATCH_URL.protocol
    headers: {} <<< DEFAULT_HEADERS <<< headers
    method: 'POST'
    body: qstring*/

download-file = (url, filename) ->
  outf = fs.createWriteStream filename
  new Promise (resolve, reject) ->
    got.stream url
      ..pipe outf
      /* download progress */
      ..on \downloadProgress ->
        process.stderr.write "\r#{(it.percent * 100).toFixed(1)}%"
      ..on \end -> process.stderr.write "\n"; resolve!
      ..on \error -> reject it



get-token = (series-id, season-no, episode-no) ->
  q-prewatch = "preWatch=true&SID=#{series-id}&season=#{season-no}&ep=#{episode-no}"

  invoke q-prewatch .then ->
    it.body

get-vid = (series-id, season-no, episode-no, token) ->
  q-watch = "watch=true&token=#{token}&serie=#{series-id}&season=#{season-no}&" + \
            "episode=#{episode-no}&auth=false&type=episode"

  invoke q-watch .then ->
    JSON.parse it.body

get-url = (vid) ->
  # at this point, vid.url is actually a hostname
  # resolve it using dns.resolve (to bypass dns blocks)
  dns-resolve-promise vid.url
  .then ([ipaddr]) ->
      console.log ipaddr
      for k, v of vid.watch
        url = new URL("http://#{ipaddr}/watch/episode/#{k}/#{vid.VID}.mp4" +
                      "?token=#{v}&time=#{vid.time}&uid=")
      url

dns-resolve-promise = (hostname) ->
  new Promise (resolve, reject) ->
    dns.resolve hostname, (err, records) ->
      if err? then reject err else resolve records


mk-filename = (series-id, season-no, episode-no) ->
  double-digit = (.toString!padStart('2', 0))
  series = db.get-series-name-from-id(series-id) ? series-id
  "#{series} S#{double-digit season-no}E#{double-digit episode-no}.mp4"

download-episode = (series-id, season-no, episode-no, existing-token) ->

  get-token-res =
    if existing-token?
      Promise.resolve existing-token
    else
      get-token series-id, season-no, episode-no .then ->
        token = it
        console.log "Token: #token"
        #dotted-delay 30000 .then -> token
        token

  delayed-retries ->
      get-token-res.then (token) ->
        get-vid series-id, season-no, episode-no, token .then ->
          console.log it
          if it.url?
            get-url it .then (url) ->
              if url?
                download-file url, "/tmp/#{mk-filename series-id, season-no, episode-no}"
          else
              Promise.reject!

      #.catch -> console.error it


delayed-retries = (attempt, interval=5000, timeout=40000) ->
  start-time = Date.now();
  new Promise (resolve, reject) ->
      f = ->
          if Date.now() - start-time > timeout then reject!
          else
              attempt!then resolve
              .catch -> setTimeout f, interval

      f!

dotted-delay = (total, interval=5000) ->
  new Promise (resolve, reject) ->
    f = (ms) ->
      console.log '.'
      if ms <= 0 then resolve!
      else setTimeout (-> f Math.max(ms - interval, 0)), Math.min(ms, interval)
    f total


chain-actions = (actions) ->
  p = Promise.resolve!
  for let a in actions
    p := p.then a
  p



if module.id == '.'
  dns = require 'dns'
  dns.setServers ['8.8.8.8']

  l = db.get-series-id-from-name

  args = process.argv[3 to]

  token = args.0

  #download-episode l("oto"), 1, 6, token
  download-episode l("ish"), 1, 6, token
  #download-episode l("cond"), 1, 10, token
