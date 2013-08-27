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
        if (this.has_key(key)) {
            cb(key, this.values[key]);
        }
    }
};
$.Map.prototype.get = function(key) {
    return this.values[key];
};
$.Map.prototype.get_object = function() {
    return this.values;
};
$.Map.prototype.has_key = function(key) {
    return Object.prototype.hasOwnProperty.call(this.values, key);
};
$.Map.prototype.setdefault = function(key, default_val) {
    default_val = default_val || null;
    if (!this.has_key(key)) {
        this.values[key] = default_val;
    }
    return this.values[key];
};
$.Map.prototype.valueOf = function() {
    var internal = {};
    this.foreach(function(key, value) {
        internal[key] = value.valueOf();
    });
    return internal;
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
$.Set.prototype.valueOf = function() {
    return this.get_array();
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


// build a list of node types we want to visit
var get_src = function(e) { return e.src; };
var visit = new $.Map({
    '*': new $.Map({'img-src': function(e) {
        /** Retrieve all background images. */
        var bg = window.getComputedStyle(e, false).backgroundImage;
        var match = bg.match(/url\('?([^)]*[^']+)'?\)/);
        return (match) ? match[1] : undefined;
    }}),
    'SCRIPT': new $.Map({'script-src': get_src}),
    'IMG': new $.Map({'img-src': get_src}),
});


window.addEventListener('load', function() {
    // document.styleSheets[0].href

    // all gathered sources
    var sources = new $.Map();

    // visit all nodes
    var nodes = document.getElementsByTagName('*');
    var node = null;
    var store_in_sources = function(directive, func) {
        var uri = func(node);
        if (uri) {
            sources.setdefault(directive, new $.Set()).add(uri);
        }
    };
    for (var i = 0; i < nodes.length; i++) {
        if (nodes[i].tagName) {
            node = nodes[i];
            visit.get('*').foreach(store_in_sources);
            if (visit.has_key(nodes[i].tagName)) {
                visit.get(nodes[i].tagName).foreach(store_in_sources);
            }
        }
    }

    // create JSON string
    var sources = JSON.stringify(sources.valueOf());
    var uri = location.pathname + location.search;
    var postdata = new $.Map({'uri': uri, 'sources': sources})
    $.net.post(report_uri, postdata);
});


})();