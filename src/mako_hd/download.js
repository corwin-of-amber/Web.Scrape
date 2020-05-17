#!/usr/bin/env node
var fs = require('fs');
//req = JSON.parse(fs.readFileSync("./chunklist.json"));


var http = require("http"),
    url = require('url');

function get_filename(fpath) {
    var uri = /^[^?]*/.exec(fpath)[0];  // remove query
    return /[^/]+$/.exec(uri)[0];
}
/*
function get_header(res, header) {  // the missing IncomingMessage method
    for (i = 0; i < res.headers.length; ++i) {
        if (res.headers[i]
}
*/

async function main() {

    var argv = require('yargs').command('$0 [filename] [--start-at segment] [--stop-at segment] [--entries list-filename]', '')
               .default({filename: './chunklist.json', 'start-at': 0})
               .argv;

    console.log(argv);

    var reqData = JSON.parse(fs.readFileSync(argv.filename));

    var req = {
        ...url.parse(reqData.url),
        //...reqData,
        headers: reqData.headers
    };
    /*
    uri = url.parse(reqData.url);
    req.host = uri.hostname;
    req.port = uri.port || 80;
    req.path = uri.path;
    */
    req.protocol = 'http:';
    req.path = req.path.replace(/index_\d/, "index_3")
                       .replace(/chunklist_b\d+/, "chunklist_b2200000");

    query = (/[?].*/.exec(req.path) || [""])[0];


    outdir = "/tmp/mako_hd";

    mkdirp = require('mkdirp');
    mkdirp(outdir);


    console.log(req);

    try {
        if (argv['entries']) {
            var entries = parseList(fs.readFileSync(argv['entries'], 'utf-8'));
            downloadList(entries, reqData.url, reqData.headers, argv['start-at'], argv['stop-at']);
        }
        else {
            var entries = await fetchList(reqData.url, reqData.headers);
            //console.log(entries);

            entries = await fetchList(url.resolve(reqData.url, entries.slice(-1)[0]), reqData.headers);
            //console.log(entries);

            downloadList(entries, reqData.url, reqData.headers, argv['start-at'], argv['stop-at']);
        }
    }
    catch (e) {
        if (!(e instanceof HttpFailed)) throw e;
    }
        /*
        var post_req = http.request(req, function(res) {
            console.log(`${res.statusCode} ${res.statusMessage}`);
            if (res.statusCode == 200) {
                var body = "";
                res.on('data', function(data) { body += data; });
                res.on('end', function() {
                    //console.log(body);
                    var entries = parseList(body)
                    downloadList(req, entries, argv['start-at'], argv['stop-at']);
                });
            }
        });
        post_req.end();*/
    
}

class HttpFailed { }

function fetchText(uri, headers) {
    var options = { ...url.parse(uri), protocol: 'http:', headers };

    return new Promise((resolve, reject) => {
        var req = http.request(options, function(res) {
            console.log(`${res.statusCode} ${res.statusMessage}`);
            if (res.statusCode == 200) {
                var body = "";
                res.on('data', function(data) { body += data; });
                res.on('end', function() {
                    //console.log(body);
                    resolve(body);
                });
            }
            else reject(new HttpFailed());
        });
        req.end();
    });
}

async function fetchList(uri, headers) {
    return parseList(await fetchText(uri, headers));
}

function parseList(body) {
    return body.split(/\n/).filter((l) => !/^(#|\s*$)/.exec(l));
}

function downloadList(entries, baseUri, headers, startAt, stopAt) {
    /* Write a playlist (ffmpeg file list format) */
    fs.writeFileSync("list", entries.map((l) => `file ${outdir}/${get_filename(l)}\n`).join(""))

    //console.log(entries);
    
    function downloadFragment(i) {
        let uri = entries[i];
        if (!uri) return;

        console.log(`${i}/${entries.length}`);
        console.log(uri);

        uri = url.resolve(baseUri, uri);
        
        /*
        req.path = (/http:/.exec(uri)) ? uri : req.path.replace(/[/][^/]+$/, `/${uri}`);
        if (!/[?]/.exec(req.path))
            req.path += query;
        if (req.path != uri)
            console.log(req.path);

        req.timeout = 2000;
        */
        var options = { ...url.parse(uri), protocol: 'http:', headers, timeout: 2000 };        
        
        let frag_req = http.request(options, function(res) {
            let total_size = parseInt(res.headers['content-length']);
            let filename = get_filename(uri);
            let recvd_size = 0, cont = false;
            res.on('data', (data) => {
                recvd_size += data.length;
                if (!cont && recvd_size < 100) console.log(data.toString());
                else { 
                    cont = true;
                    process.stderr.write(`\r${recvd_size} ${(recvd_size * 100 / total_size).toFixed(1)}% `); 
                }
            });
            res.pipe(fs.createWriteStream(`${outdir}/${filename}`));
            res.on('end', () => {
                if (cont && recvd_size >= total_size * 0.99) {
                    console.log("done");
                    if (i != stopAt)
                        downloadFragment(i+1);
                }
                else {
                    console.log("throttle...");
                    setTimeout(() => { downloadFragment(i); }, 10000);
                }
            });
        });
        frag_req.on('error', (err) => {
            console.log('error while downloading:')
            console.error(err);
            console.log('retry...');
            setTimeout(() => { downloadFragment(i); }, 1000);
        });
        frag_req.on('timeout', () => frag_req.abort());
        frag_req.end();
    }

    downloadFragment(startAt);
}


if (module.id === '.')
    main();

