require! fs
RegExp.quote = require 'regexp-quote'



read = -> JSON.parse(fs.readFileSync('db.json', 'utf-8'))
write = (db_=db) ->
  fs.writeFileSync 'db.json', JSON.stringify(db, , 2)


db = read!

get-series-id-from-name = (keyword) ->
  re = // #{RegExp.quote(keyword)} //i
  for [code, name] in db.series
    if re.exec(name) then return code
  throw new Error("series not found by keyword '#{keyword}'")

get-series-name-from-id = (code) ->
  for [code_, name] in db.series
    if code ~= code_ then return name
  throw new Error("no series code #{code}")

get-series-data = (code) ->
  for [code_, name, data] in db.series
    if code ~= code_ then return data ? {}
  throw new Error("no series code #{code}")

set-series-data = (code, data) ->
  for entry in db.series
    if code ~= entry[0] then entry[2] = data ; return
  throw new Error("no series code #{code}")



export get-series-id-from-name, get-series-name-from-id, get-series-data, set-series-data, write
