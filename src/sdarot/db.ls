require! fs
RegExp.quote = require 'regexp-quote'



read = -> JSON.parse(fs.readFileSync('db.json'))


db = read!

get-series-id-from-name = (keyword) ->
  re = // #{RegExp.quote(keyword)} //i
  for [code, name] in db.series
    if re.exec(name) then return code

get-series-name-from-id = (code) ->
  for [code_, name] in db.series
    if code ~= code_ then return name


export get-series-id-from-name, get-series-name-from-id
