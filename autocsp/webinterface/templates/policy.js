(function() {
/** Policy generation script. Will retrieve CSP directive URIs from the DOM. */
'use strict';


var DEBUG = {{ debug|int }};
if (DEBUG) {
    console.warn('autoCSP is in debug mode.');
}


(function() {
    /** Delete this <script> element from DOM (first script on page). */
    var this_element = document.getElementsByTagName('script')[0];
    this_element.parentNode.removeChild(this_element);
})();


// shortcut functions
var $ = {
    empty: function(value) {
        /** Sane emptiness check. $.empty([]) == true, $.empty({}) == true */
        if (value === null || value === undefined ||
            (value.constructor !== Boolean &&
             ((value.constructor === Array && !value.length) ||
              (value.constructor === Object &&
               value.toString() == '[object Object]' &&
               !Object.keys(value).length) || !value))) {
            return true;
        }
        return false;
    },
    toAbsoluteUri: function(uri) {
        var a = document.createElement('a');
        a.href = uri;
        return a.href;
    },
};


// Array functions
var $a = {
    add: function(array, value) {
        /** If value, adds to array, if array adds all values to array. */
        if (value.constructor === Array) {
            for (var i = 0; i < value.length; i++) {
                array.push(value[i]);
            }
        } else {
            array.push(value);
        }
    },
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
    setDefault: function(object, key, default_val) {
        /** Returns a object key and sets it if it does not exist, yet. */
        default_val = default_val || null;
        if (!$o.in(object, key)) {
            object[key] = default_val;
        }
        return object[key];
    },
};


// String functions
var $s = {
    startsWith: function(str, startstr) {
        return str.slice(0, startstr.length) === startstr;
    },
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


// will contain a Map of Node types we want to visit
var visit = null;


/** Contains all functions used to extract sources. **/
(function() {
    var sanitizeUri = function(uri) {
        /** Clears data from data-URIs. */
        if (!$.empty(uri)) {
            if ($s.startsWith(uri, 'data:')) {
                return 'data:';
            }
        }
        return uri;
    };

    var getSrc = function(e) {
        return sanitizeUri(e.src);
    };
    var getAppletAttr = function(e) {
        var uris = [];
        $a.forEach(['code', 'archive', 'codebase'], function(prop) {
            if (e[prop]) {
                uris.push(sanitizeUri($.toAbsoluteUri(e[prop])));
            }
        });
        return uris;
    };
    var frames = [];
    var getFrameSrc = function(e) {
        if (!$a.in(frames, e)) {
            frames.push(e);
            var blocknext = false;
            e.addEventListener('load', function() {
                if (blocknext) {
                    blocknext = false;
                } else {
                    // re-set the src to the navigated location to trigger a
                    // Mutation Observer attribute change
                    // XXX: can cause problems
                    this.src = e.contentWindow.location;
                    blocknext = true;
                }
            });  
        }
        return getSrc(e);
    };
    var getObjectData = function(e) {
        return sanitizeUri(e.data);
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
        'APPLET': {'object-src': getAppletAttr},
        'AUDIO': {'media-src': getSrc},
        'EMBED': {'object-src': getSrc},
        'FRAME': {'frame-src': getFrameSrc},
        'IFRAME': {'frame-src': getFrameSrc},
        'IMG': {'img-src': getSrc},
        'LINK': {'img-src': getIcon, 'style-src': checkStyles},
        'OBJECT': {'object-src': getObjectData},
        'SCRIPT': {'script-src': getSrc},
        'SOURCE': {'media-src': getSrc},
        'STYLE': {'style-src': checkStyles},
        'TRACK': {'media-src': getSrc},
        'VIDEO': {'media-src': getSrc},
    };
})();


window.addEventListener('load', function() {
    // current path
    var uri = location.pathname + location.search;

    var inferRules = function(nodes) {
        /** Infers CSP rules from given nodes with the visit list. */
        var rules = {};
        var node = null;
        var store_in_sources = function(directive, func) {
            var uri = func(node);
            if (!$.empty(uri)) {
                var list = $o.setDefault(rules, directive, []);
                if (!$a.in(list, uri)) {
                    $a.add(list, uri);
                }
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
        return rules;
    };
    var processNodes = function(nodes) {
        /** Retrieves policy rules from nodes and POSTs to backend. */
        var rules = inferRules(nodes);
        if ($.empty(rules)) {
            // don't POST empty JSON response
            return;
        }
        var rules = JSON.stringify(rules.valueOf());
        if (DEBUG) {
            console.info('Sending data to backend for ' + uri + ':\n' + rules);
        }
        $n.post('{{ report_uri }}', {'uri': uri, 'sources': rules});
    };


    if (DEBUG) {
        console.log('Start processing all nodes to infer rules...');
        var startTime = Date.now();
    }
    processNodes(document.getElementsByTagName('*'));
    if (DEBUG) {
        var delta = Date.now() - startTime;
        console.log('Finished processing all nodes in ' + delta + ' ms.');
    }

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