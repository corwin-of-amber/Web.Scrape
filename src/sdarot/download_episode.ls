fs = require 'fs'
http = require 'http'
dns = require 'dns'
{URL} = require 'url'
RegExp.quote = require 'regexp-quote'
db = require './db.ls'

require! request
require! 'request-progress'


HOST = 'zira.online'
IPADDR = '149.202.200.130'

WATCH_URL = new URL("https://#{IPADDR}/ajax/watch")

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36"

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:67.0) Gecko/20100101 Firefox/67.0"

COOKIE = 'Sdarot=Dql5fOcKxQkw391DrQwQ-nsy6hdvqaX9ySUDd1C9AwTRwy5lHEBpSt7fjcOkOOeAwxJoZwvQXSM85lEfTHEiMGHL2VBGpcdwIi%2CM1NsY1h58JqzYhTcH3hXUb%2CEA5gmy'

if db.get-cookie! then COOKIE = that


DEFAULT_HEADERS =
#      'Host': HOST
      'User-Agent': USER_AGENT
      'Cookie': COOKIE
      'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
#      'Origin': "http://#{WATCH_URL.hostname}"
      'Referer': "https://zira.online/watch/1325-%D7%90%D7%99%D7%A9-%D7%97%D7%A9%D7%95%D7%91-%D7%9E%D7%90%D7%95%D7%93-ish-hashuv-meod/season/2/episode/3"
      'X-Requested-With': 'XMLHttpRequest'
      'Accept': 'application/json, text/javascript, */*; q=0.01'
      'Connection': 'keep-alive'
#      'Accept-Language: en-US,en;q=0.5'
#      'Accept-Encoding': 'gzip, deflate'
      'TE': 'Trailers'

VID_HEADERS =
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3'
    'Accept-Encoding': 'gzip, deflate, br'


invoke = (qstring) ->
  headers =
    'Host': HOST
    'Content-Length': Buffer.byteLength(qstring)

  new Promise (resolve, reject) ->
    request do ->
      uri: WATCH_URL
      method: 'POST'
      headers: {} <<< DEFAULT_HEADERS <<< headers
      strictSSL: false
      body: qstring
    , (error, response, body) ->
      console.log response.headers
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
  console.log url.href
  opts =
      uri: url
      headers: {} <<< DEFAULT_HEADERS <<< VID_HEADERS
      strictSSL: false
  new Promise (resolve, reject) ->
    request-progress(request(opts), {throttle: 100})
      ..pipe outf
      /* download progress */
      ..on \progress ->
          process.stderr.write "\r#{(it.percent * 100).toFixed(1)}%"
      ..on \end -> process.stderr.write "\n"; resolve!
      ..on \error -> reject it



get-token = (series-id, season-no, episode-no) ->
  q-prewatch = "preWatch=true&SID=#{series-id}&season=#{season-no}&ep=#{episode-no}"

  invoke q-prewatch .then ->
    it.body

get-vid = (series-id, season-no, episode-no, token) ->
  q-watch = "watch=false&token=#{token}&serie=#{series-id}&season=#{season-no}&" + \
            "episode=#{episode-no}&type=episode"

  invoke q-watch .then ->
    JSON.parse it.body

get-url = (vid) ->
  # at this point, vid.url is actually a hostname
  # resolve it using dns.resolve (to bypass dns blocks)
  dns-resolve-promise vid.url
  .then ([ipaddr]) ->
      console.log ipaddr
      for k, v of vid.watch
        url = new URL("https://#{ipaddr}/w/episode/#{k}/#{vid.VID}.mp4" +
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
        #dotted-delay 35000 .then -> token
        token


  delayed-retries ->
      #do ->
      get-token-res.then (token) ->
        get-vid series-id, season-no, episode-no, token .then ->
          console.log it
          if it.url?
            get-url it .then (url) ->
              if url?
                download-file url, "/tmp/#{mk-filename series-id, season-no, episode-no}"
            .catch -> console.error it
          else
              Promise.reject!



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
  download-episode l("ish"), 2, 3, token
  #download-episode l("cond"), 1, 10, token

  #url = new URL('https://voldemort.sdarot.pm/w/episode/480/245754.mp4?token=tHGq336YrQiN24MfcvLUIQ&time=1561931427&uid=')
  #download-file url, '/tmp/a'
