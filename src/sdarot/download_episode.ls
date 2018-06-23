fs = require 'fs'
http = require 'http'
got = require 'got'
{URL} = require 'url'
RegExp.quote = require 'regexp-quote'



WATCH_URL = new URL('http://www.zira.online/ajax/watch')

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36"

COOKIE = '_ga=GA1.2.486464997.1518630789; Sdarot=sTpq211CqWVoLzPxyeU5Lbc358RJutZn48XkNHXwfDY1tUQSmASJrm7OzzoiFhbKlU8Au0Td5sVJhBUyi3DDVl4UE1C9YMJeyUk4UDAhOyxeUuhe7gsZdWKjZsQi0MVr; _gid=GA1.2.1224283793.1527699600; _gat=1'

DEFAULT_HEADERS =
      'User-Agent': USER_AGENT
      'Cookie': COOKIE
      'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
      'Origin': "http://#{WATCH_URL.hostname}"
      'Referer': "http://#{WATCH_URL.hostname}/watch"
#      'X-Requested-With': 'XMLHttpRequest'
#      'Accept': 'application/json, text/javascript, */*; q=0.01'
#      'Connection': 'keep-alive'
#      'Accept-Encoding': 'gzip, deflate'

SERIES_CODES =
  * [3248, "Shababnikim"]
  * [3493, "Kacha Ze"]
  * [2246, "My Successful Sisters"]
  * [3785, "Al Haspectrum"]


invoke = (qstring) ->
  headers =
    'Content-Length': Buffer.byteLength(qstring)

  got do
    host: WATCH_URL.hostname
    path: WATCH_URL.pathname
    headers: {} <<< DEFAULT_HEADERS <<< headers
    method: 'POST'
    body: qstring

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
  for k, v of vid.watch
    url = new URL("http://#{vid.url}/watch/episode/#{k}/#{vid.VID}.mp4" +
                  "?token=#{v}&time=#{vid.time}&uid=")
  url

mk-filename = (series-id, season-no, episode-no) ->
  double-digit = (.toString!padStart('2', 0))
  series = get-series-name-from-id(series-id) ? series-id
  "#{series} S#{double-digit season-no}E#{double-digit episode-no}.mp4"

download-episode = (series-id, season-no, episode-no, existing-token) ->

  get-token-res =
    if existing-token?
      Promise.resolve existing-token
    else
      get-token series-id, season-no, episode-no .then ->
        token = it
        console.log "Token: #token"
        dotted-delay 30000 .then -> token

  get-token-res.then (token) ->
    get-vid series-id, season-no, episode-no, token .then ->
      console.log it
      url = get-url it
      if url?
        download-file url, "/tmp/#{mk-filename series-id, season-no, episode-no}"

  .catch -> console.error it

dotted-delay = (total, interval=5000) ->
  new Promise (resolve, reject) ->
    f = (ms) ->
      console.log '.'
      if ms <= 0 then resolve!
      else setTimeout (-> f Math.max(ms - interval, 0)), Math.min(ms, interval)
    f total

get-series-id-from-name = (keyword) ->
  re = // #{RegExp.quote(keyword)} //i
  for [code, name] in SERIES_CODES
    if re.exec(name) then return code

get-series-name-from-id = (code) ->
  for [code_, name] in SERIES_CODES
    if code ~= code_ then return name


chain-actions = (actions) ->
  p = Promise.resolve!
  for let a in actions
    p := p.then a
  p

if module.id == '.'
  l = get-series-id-from-name

  args = process.argv[2 to]

  token = args.0

  #chain-actions [13].map (a) -> ->
  #  download-episode l("shababnikim"), 1, a

  #download-episode l("shababnikim"), 1, 11
  #download-episode l("kacha ze"), 1, 9, token
  #download-episode l("sister"), 1, 2
  download-episode l("spectrum"), 1, 5, token
