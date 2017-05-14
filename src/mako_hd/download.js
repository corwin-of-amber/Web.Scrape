var fs = require('fs');
req = JSON.parse(fs.readFileSync("./chunklist.json"));


var http = require("http"),
    url = require('url');

uri = url.parse(req.url);
req.host = uri.hostname;
req.port = uri.port || 80;
req.path = uri.path;

query = (/[?].*/.exec(req.path) || [""])[0];

function get_filename(fpath) {
    return /^[^?]*/.exec(/[^/]+$/.exec(fpath)[0])[0];
}

outdir = "/tmp/mako_hd";


console.log(req);
var post_req = http.request(req, function(res) {
    //console.log(res);
    var body = "";
    res.on('data', function(data) { body += data; });
    res.on('end', function() {
        //console.log(body);
        var lines = body.split(/\n/).filter((l) => !/^(#|\s*$)/.exec(l));

        /* Write a playlist (ffmpeg file list format) */
        fs.writeFileSync("list", lines.map((l) => `file ${outdir}/${get_filename(l)}\n`).join(""))

        console.log(lines);
        function downloadFragment(i) {
            let line = lines[i];
            if (!line) return;
            console.log(line);
            req.path = (/http:/.exec(line)) ? line : req.path.replace(/[/][^/]+$/, `/${line}`);
            req.path += query;
            console.log(req.path);
            let frag_req = http.request(req, function(res) {
                //console.log(res);
                let filename = get_filename(line);
                res.pipe(fs.createWriteStream(`${outdir}/${filename}`));
                res.on('end', () => {
                    console.log("done");
                    downloadFragment(i+1);
                });
            });
            frag_req.end();
        }
        downloadFragment(0);
    });

});
post_req.end();
