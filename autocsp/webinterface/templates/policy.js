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


$.Set = function(values) {
    var values = values || [];
    this.values = {};
    for (var i = 0; i < values.length; i++) {
        this.values[values[i]] = true;
    }
};
$.Set.prototype.add = function(value) {
    this.values[value] = true;
};
$.Set.prototype.get_array = function() {
    return Object.keys(this.values);
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
    var uris = new $.Set();
    for (var i = 0; i < nodes.length; i++) {
        var uri = nodes[i][attribute];
        if (uri) {
            uris.add(uri);
        }
    }
    return uris.get_array();
};


// variable definitions
var report_uri = '{{ report_uri }}';
var self_uri = location.protocol + '//' + location.hostname +
               (location.port ? ':' + location.port : '')


window.addEventListener('load', function() {
    var sources = {};
    var visit = new $.Map({
        'script': 'src',
        'img': 'src'
    });
    visit.foreach(function(key, value) {
        var uris = gather_uris(document.querySelectorAll(key), value);
        if (uris.length) {
            sources[key] = uris;
        }
    });
    var uri = location.pathname + location.search;
    var postdata = new $.Map({'uri': uri, 'sources': JSON.stringify(sources)})
    $.net.post(report_uri, postdata);
});


})();