(function() {


(function() {
    /** Delete this <script> element from DOM (first script on page). */
    var this_element = document.getElementsByTagName('script')[0];
    this_element.parentNode.removeChild(this_element);
})();


// internal implementation
var $ = {
    empty: function(value) {
        /** Checks if the element is empty. */
        if (value === null || value === undefined ||
            (value.constructor === Array && !value.length) || !value) {
            return true;
        }
        return false;
    },
    toAbsoluteURI: function(uri) {
        /** Makes an absolute URI from a relative one. */
        var a = document.createElement('a');
        a.href = uri;
        return a.href;
    },
};


// Array functions
$.a = {
    forEach: function(array, callback) {
        /** Calls forEach on arrays and array-like objects. */
        Array.prototype.forEach.call(array, callback);
    },
    in: function(array, value) {
        /** Checks if value can be found in array. */
        return Array.prototype.indexOf.call(array, value) > -1;
    },
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
    /** Adds a new element or a list of elements to the Set. */
    if ($.empty(value)) {
        return false;
    }
    if (value.constructor === Array) {
        for (var i = 0; i < value.length; i++) {
            this.add(value[i]);
        }
    } else {
        this.values[value] = true;
    }
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


// will contain a Map of Node types we want to visit
var visit = null;


/** Contains all functions used to extract sources. **/
(function() {
    var getSrc = function(e) {
        return e.getAttribute('src');
    };
    var getBackgroundImage = function(e) {
        /** Retrieve all background image URIs. */
        var bg = window.getComputedStyle(e, false).backgroundImage;
        var match = bg.match(/url\('?([^)]*[^']+)'?\)/);
        return (match) ? match[1] : null;
    };
    var getIcon = function(e) {
        /** Check if <link>-element is icon and return href. */
        if (e.getAttribute('rel') === 'icon') {
            var uri = e.getAttribute('href');
            if (!$.empty(uri)) { return $.toAbsoluteURI(uri); }
        }
        return null;
    };

    // remembers all stylesheets (prevent crawling rules a second time)
    var styles = [];
    var appendStyle = function(stylesheet, newStyles) {
        /** If a stylesheet was found this will check if its new and recurse. */
        // unfortunately we cannot know if we already visited an inline style
        if (!$.a.in(styles, stylesheet.href)) {
            // don't add to styles list if inline
            if (!$.empty(stylesheet.href)) {
                newStyles.push(stylesheet.href);
                styles.push(stylesheet.href);
            }
            for (var i = 0; i < stylesheet.rules.length; i++) {
                // @import rules are always on top so break if no import
                if (stylesheet.rules[i].constructor !== CSSImportRule) {
                    break;
                }
                // recurse into stylesheet (could contain more @imports)
                appendStyle(stylesheet.rules[i].styleSheet, newStyles);
            }
        }
    };
    var checkStyles = function(e) {
        /** Checks for new stylesheets in document.styleSheets. */
        newStyles = [];
        $.a.forEach(document.styleSheets, function(stylesheet) {
            appendStyle(stylesheet, newStyles);
        });
        return newStyles;
    };

    visit = new $.Map({
        '*': new $.Map({'img-src': getBackgroundImage}),
        'IMG': new $.Map({'img-src': getSrc}),
        'LINK': new $.Map({'img-src': getIcon, 'style-src': checkStyles}),
        'SCRIPT': new $.Map({'script-src': getSrc}),
        'STYLE': new $.Map({'style-src': checkStyles}),
    });
})();


var gather_uris = function(nodes) {
    /** Use visit list to find interesting nodes and extract source uris. */
    var sources = new $.Map();
    var node = null;
    var store_in_sources = function(directive, func) {
        var uri = func(node);
        if (!$.empty(uri)) {
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
    var uri = location.pathname + location.search;
    var gather_and_post = function(nodes) {
        var sources = gather_uris(nodes);
        if (!sources.length) {
            return;
        }
        var sources = JSON.stringify(sources.valueOf());
        console.log(sources);
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