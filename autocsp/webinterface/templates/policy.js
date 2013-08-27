(function() {


(function() {
    /** Delete this <script> element from DOM (first script on page). */
    var this_element = document.getElementsByTagName('script')[0];
    this_element.parentNode.removeChild(this_element);
})();


// internal implementations object
var $ = {};


// shortcuts
$.to_absolute = function(uri) {
    /** Makes an absolute URI from a relative one. */
    var a = document.createElement('a');
    a.href = uri;
    return a.href;
};


$.Map = function(values) {
    /** Maps keys to values without the shenanigans of JavaScript. */
    this.values = values || {};
    this.length = Object.keys(this.values).length;
};
$.Map.prototype.add = function(key, value) {
    this.values[key] = value;
    this.length++;
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
        this.length++;
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


// variable definitions
var report_uri = '{{ report_uri }}';
var self_uri = location.protocol + '//' + location.hostname +
               (location.port ? ':' + location.port : '') + '/';


// build a list of node types we want to visit
var get_src = function(e) { return e.src; };
var visit = new $.Map({
    '*': new $.Map({'img-src': function(e) {
        /** Retrieve all background images. */
        var bg = window.getComputedStyle(e, false).backgroundImage;
        var match = bg.match(/url\('?([^)]*[^']+)'?\)/);
        return (match) ? match[1] : null;
    }}),
    'SCRIPT': new $.Map({'script-src': get_src}),
    'IMG': new $.Map({'img-src': get_src}),
    'LINK': new $.Map({'img-src': function(e) {
        /** Check if is icon and return href. */
        if (e.getAttribute('rel') === 'icon') {
            var uri = e.getAttribute('href');
            if (uri) {
                return $.to_absolute(uri);               
            }
        }
        return null;
    }}),
});
var gather_uris = function(nodes) {
    /** Use visit list to find interesting nodes and extract source uris. */
    var sources = new $.Map();
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
            if (visit.has_key(node.tagName)) {
                visit.get(node.tagName).foreach(store_in_sources);
            }
        }
    }
    return sources;
};


window.addEventListener('load', function() {
    // document.styleSheets[0].href

    var uri = location.pathname + location.search;
    var gather_and_post = function(nodes) {
        var sources = gather_uris(nodes);
        if (!sources.length) {
            return;
        }
        var sources = JSON.stringify(sources.valueOf());
        var postdata = new $.Map({'uri': uri, 'sources': sources})
        $.net.post(report_uri, postdata);
    };

    // visit all nodes
    gather_and_post(document.getElementsByTagName('*'));

    // register an observer for future changes
    var observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            var nodes = (mutation.type === 'childList') ? mutation.addedNOdes :
                                                          [mutation.target];
            gather_and_post(nodes);
        });
    });
    observer.observe(document.body.parentNode,
                     {subtree: true, childList: true, attributes: true});
});


})();