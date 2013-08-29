(function() {
/** Policy generation script. Will retrieve CSP directive URIs from the DOM. */
'use strict';


(function() {
    /** Delete this <script> element from DOM (first script on page). */
    var this_element = document.getElementsByTagName('script')[0];
    this_element.parentNode.removeChild(this_element);
})();


// shortcut functions
var $ = {
    empty: function(value) {
        if (value === null || value === undefined ||
            (value.constructor === Array && !value.length) || !value) {
            return true;
        }
        return false;
    },
    /*
    toAbsoluteURI: function(uri) {
        var a = document.createElement('a');
        a.href = uri;
        return a.href;
    },*/
};


// Array functions
var $a = {
    forEach: function(array, callback) {
        /** Calls forEach on arrays and array-like objects. */
        Array.prototype.forEach.call(array, callback);
    },
    in: function(array, value) {
        /** Checks if value can be found in array. */
        return Array.prototype.indexOf.call(array, value) > -1;
    },
};


// Object functions
var $o = {
    forEach: function(object, callback) {
        for (var key in object) {
            if ($o.in(object, key)) {
                callback(key, object[key]);
            }
        }
    },
    in: function(object, key) {
        /** Returns if an key exists in the object. */
        return Object.prototype.hasOwnProperty.call(object, key);
    },
};


// String functions
var $s = {
    startsWith: function(str, startstr) {
        return str.slice(0, startstr.length) === startstr;
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


// Network functions
var $n = {
    get: function(url, callback) {
        (new $n.Request(url, callback)).get();
    },
    post: function(url, data, callback) {
        /** POSTS to the URL and url-encodes the data object. */
        var components = [];
        $o.forEach(data, function(key, value) {
            components.push(window.encodeURIComponent(key) + '=' +
                            window.encodeURIComponent(value));
        });
        (new $n.Request(url, callback)).post(components.join('&'));
    }, 
};
$n.Request = function(url, callback) {
    callback = callback || function () {};
    this.url = url;
    this.xhr = new XMLHttpRequest();
    this.xhr.addEventListener('readystatechange', function() {
        if (this.readyState === 4) {
            callback(this.responseText);
        }
    });
};
$n.Request.prototype.get = function() {
    this.xhr.open('GET', this.url);
    this.xhr.send();
};
$n.Request.prototype.post = function(data) {
    data = data || '';
    this.xhr.open('POST', this.url);
    this.xhr.send(data);
};


// variable definitions
//var self_uri = location.protocol + '//' + location.hostname +
//               (location.port ? ':' + location.port : '') + '/';


// will contain a Map of Node types we want to visit
var visit = null;


/** Contains all functions used to extract sources. **/
(function() {
    var sanitizeUri = function(uri) {
        /** Detects data: URIs and just returns data: in that case */
        if ($.empty(uri) || !$s.startsWith(uri, 'data:')) {
            return uri;
        }
        // oh, it's a data URI
        return 'data:';
    };

    var getSrc = function(e) {
        return sanitizeUri(e.src);
    };
    var getBackgroundImage = function(e) {
        /** Retrieve all background image URIs. */
        var bg = window.getComputedStyle(e, false).backgroundImage;
        var match = bg.match(/url\('?([^)]*[^']+)'?\)/);
        return (match) ? sanitizeUri(match[1]) : null;
    };
    var getIcon = function(e) {
        return (e.rel === 'icon') ? sanitizeUri(e.href) : null;
    };

    // remembers all stylesheets (prevent crawling rules a second time)
    var styles = [];
    var appendStyle = function(stylesheet, newStyles) {
        /** If a stylesheet was found this will check if its new and recurse. */
        // unfortunately we cannot know if we already visited an inline style
        var uri = sanitizeUri(stylesheet.href);
        if (!$a.in(styles, uri)) {
            // don't add to styles list if inline
            if (!$.empty(uri)) {
                newStyles.push(uri);
                styles.push(uri);
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
        var newStyles = [];
        $a.forEach(document.styleSheets, function(stylesheet) {
            appendStyle(stylesheet, newStyles);
        });
        return newStyles;
    };

    visit = {
        '*': {'img-src': getBackgroundImage},
        'IMG': {'img-src': getSrc},
        'LINK': {'img-src': getIcon, 'style-src': checkStyles},
        'SCRIPT': {'script-src': getSrc},
        'STYLE': {'style-src': checkStyles},
    };
})();


window.addEventListener('load', function() {
    var inferRules = function(nodes) {
        /** Infers CSP rules from given nodes with the visit list. */
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
                $o.forEach(visit['*'], store_in_sources);
                if ($o.in(visit, node.tagName)) {
                    $o.forEach(visit[node.tagName], store_in_sources);
                }
            }
        }
        return sources;
    };

    var uri = location.pathname + location.search;
    var processNodes = function(nodes) {
        /** Retrieves policy rules from nodes and POSTs to backend. */
        var rules = inferRules(nodes);
        if ($.empty(rules)) {
            // don't POST empty JSON response
            return;
        }
        var rules = JSON.stringify(rules.valueOf());
        console.log(rules);
        $n.post('{{ report_uri }}', {'uri': uri, 'sources': rules});
    };

    // visit all nodes at load one time
    processNodes(document.getElementsByTagName('*'));

    // register an observer for future changes (tree mod and attributes)
    var observer = new MutationObserver(function(mutations) {
        $a.forEach(mutations, function(mutation) {
            var nodes = (mutation.type === 'childList') ? mutation.addedNodes :
                                                          [mutation.target];
            processNodes(nodes);
        });
    });
    observer.observe(document.body.parentNode,
                     {subtree: true, childList: true, attributes: true});
});


})();