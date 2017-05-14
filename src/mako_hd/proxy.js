// HTTP forward proxy server that can also proxy HTTPS requests
// using the CONNECT method

// requires https://github.com/nodejitsu/node-http-proxy

var httpProxy = require('http-proxy'),
    url = require('url'),
    net = require('net'),
    http = require('http');

process.on('uncaughtException', logError);

function truncate(str) {
    var maxLength = 64;
    return (str.length >= maxLength ? str.substring(0,maxLength) + '...' : str);
}

function logRequest(req) {
    console.log(req.method + ' ' + truncate(req.url) + ' [' + req.headers.host + ']');
    if (/entitlements|makostore-/.exec(req.url)) { 
        for (var i in req.headers)
            console.log(' * ' + i + ': ' + truncate(req.headers[i]));
        // As curl
        if (req.method == "POST") {
            // Read the data
            body = '';
            req.on('data', function(data) { body += data; });
            req.on('end', function() {
                console.log(`% ${requestToCurl(req, body)}`);
                fs = require('fs');
                req = {url: req.url, headers: req.headers, data: body};
                fs.writeFileSync("/tmp/req.json", JSON.stringify(req));
            });
        }
        else {
            console.log(`% ${requestToCurl(req)}`);
            fs = require('fs');
            req = {url: req.url, headers: req.headers, data: req.data};
            fs.writeFileSync("/tmp/req.json", JSON.stringify(req));
        }
    }
    if (/[/](chunklist_b2200000|index_2_av)\.m3u8/.exec(req.url)) {
        req = {url: req.url, headers: req.headers};
        fs.writeFileSync("./chunklist.json", JSON.stringify(req));
    }
}

function requestToCurl(req, post_data) {
    function fmt_hdr(hdr) { 
        return `-H '${hdr[0]}: ${hdr[1]}'`;
    }
    function fmt_data(data) {
        return data ? `--data '${data}'` : '';
    }
    return `curl '${req.url}' ${Object.entries(req.headers).map(fmt_hdr).join(" ")} ${fmt_data(post_data)}`;
}

function logError(e) {
    console.warn('*** ' + e);
}

// this proxy will handle regular HTTP requests
//var regularProxy = new httpProxy.RoutingProxy();
var regularProxy = httpProxy.createProxyServer({});

// standard HTTP server that will pass requests 
// to the proxy
var server = http.createServer(function (req, res) {
  logRequest(req);
  if (/isAbroad/.exec(req.url)) {
    res.write("0"); res.end();
  }
  else if (true || /entitlementsServices/.exec(req.url)) {
    secondaryProxy(req, res);
  }
  else {
    //uri = url.parse(req.url);
    regularProxy.web(req, res, {
        //host: uri.hostname,
        //port: uri.port || 80,
        target: req.url.replace('https:', 'http:'), //'http://' + req.headers.host
        prependPath: false
    });
  }
});

function secondaryProxy(req, res) {
    req.headers['Host'] = "mass.mako.co.il";
    //console.log(req);

    host = "localhost"; port = 8070;

    var options = {
        method: req.method,
        host: host,
        port: port,
        path: req.url,
        headers: req.headers
    };
    var post_req = http.request(options, function(_res) {
            //console.log(res);
            Object.entries(_res.headers).forEach(([k,v]) => {
                res.setHeader(k, v);
            });
//            res.headers = _res.headers;
            _res.pipe(res);
            });
    req.pipe(post_req);
    //post_req.write(req.data);
    //post_req.end();
}

// when a CONNECT request comes in, the 'upgrade'
// event is emitted
server.on('connect', function(req, socket, head) {
    logRequest(req);
    // URL is in the form 'hostname:port'
    var parts = req.url.split(':', 2);
    // open a TCP connection to the remote host
    var conn = net.connect(parts[1], parts[0], function() {
        // respond to the client that the connection was made
        socket.write("HTTP/1.1 200 OK\r\n\r\n");
        // create a tunnel between the two hosts
        socket.pipe(conn);
        conn.pipe(socket);
    });
});

server.listen(8080);
