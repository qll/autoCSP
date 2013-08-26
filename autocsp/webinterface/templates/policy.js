(function() {


(function() {
    /** Delete this <script> element from DOM (first script on page). */
    var this_element = document.getElementsByTagName('script')[0];
    this_element.parentNode.removeChild(this_element);
})();


// internal implementations object
var $ = {};


$.Map = function(values) {
    /** Maps keys to values without the shenanigans of JavaScript. */
    this.values = values || {};
};
$.Map.prototype.add = function(key, value) {
    this.values[key] = value;
};
$.Map.prototype.foreach = function(cb) {
    for (var key in this.values) {
        if (this.values.hasOwnProperty(key)) {
            cb(key, this.values[key]);
        }
    }
};
$.Map.prototype.get_object = function() {
    return this.values;
};


$.net = {};
$.net.Request = function(url, cb) {
    cb = cb || function () {};
    this.url = url;
    this.xhr = new XMLHttpRequest();
    this.xhr.addEventListener('readystatechange', function() {
        if (this.readyState === 4) {
            cb(this.responseText);
        }
    });
};
$.net.Request.prototype.get = function() {
    this.xhr.open('GET', this.url);
    this.xhr.send();
}
$.net.Request.prototype.post = function(data) {
    this.xhr.open('POST', this.url);
    this.xhr.send(data);
}
$.net.get = function(url, cb) {
    (new $.net.Request(url, cb)).get();
};
$.net.post = function(url, data, cb) {
    var components = [];
    data.foreach(function(key, value) {
        components.push(encodeURIComponent(key) + '=' +
                        encodeURIComponent(value));
    });
    (new $.net.Request(url, cb)).post(components.join('&'));
};


var gather_uris = function(nodes, attribute) {
    var uris = {};
    for (var i = 0; i < nodes.length; i++) {
        var uri = nodes[i][attribute];
        if (uri) {
            uris[uri] = (uri in uris) ? uris[uri] + 1 : 1;
        }
    }
    return uris;
};


// variable definitions
var report_uri = '{{ report_uri }}';


window.addEventListener('load', function() {
    var sources = {};
    var visit = new $.Map({
        'script': 'src',
        'img': 'src'
    });
    visit.foreach(function(key, value) {
        sources[key] = gather_uris(document.querySelectorAll(key), value);
    });
    var uri = location.protocol + '//' + location.hostname +
              (location.port ? ':' + location.port : '') + location.pathname +
              location.search;
    var postdata = new $.Map({'uri': uri, 'sources': JSON.stringify(sources)})
    $.net.post(report_uri, postdata);
});


})();