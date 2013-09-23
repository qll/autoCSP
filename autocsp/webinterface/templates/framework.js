(function() {
'use strict';


var request_id = '';
(function() {
    /** Delete this <script> element from DOM (first script on page). */
    var this_element = document.getElementsByTagName('script')[0];
    request_id = this_element.dataset.id;
    this_element.parentNode.removeChild(this_element);
})();


// current path
var document_uri = location.pathname + location.search;


{{ sha256js|safe }}


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
    log: function(msg, type) {
        /** Log function which logs only when DEBUG is enabled. */
        type = type || 'log';
        if ({{ debug|int }}) {
            console[type](msg);
        }
    },
    toAbsoluteUri: function(uri) {
        var a = document.createElement('a');
        a.href = uri;
        return a.href;
    },
    sendToBackend: function(data, report_uri) {
        /** POSTs data to backend. */
        if ($.empty(data)) {
            // don't POST empty JSON response
            return;
        }
        var data = JSON.stringify(data);
        $.log('Sending from ' + document_uri + ' to ' + report_uri + ':\n' +
              data);
        $n.post(report_uri, {'id': request_id, 'uri': document_uri,
                             'data': data});
    },
    processNodes: function(nodes, visit, checkfunc) {
        /** Visits all nodes and builds a list of visit return values. */
        var data = {};
        var checkfunc = checkfunc || function() { return true; };
        var node = null;
        var store_in_data = function(directive, getter) {
            var value = getter(node);
            var isArray = value && value.constructor === Array;
            if (isArray) {
                value = value.filter(checkfunc);
            }
            if (!$.empty(value) && (isArray || checkfunc(value))) {
                var list = $o.setDefault(data, directive, []);
                if (!$a.in(list, value)) {
                    $a.add(list, value);
                }
            }
        };
        for (var i = 0; i < nodes.length; i++) {
            if (nodes[i].tagName) {
                node = nodes[i];
                $o.forEach(visit['*'], store_in_data);
                if ($o.in(visit, node.tagName)) {
                    $o.forEach(visit[node.tagName], store_in_data);
                }
            }
        }
        return data;
    },
    matchesSelector: function(node, selector) {
        /** Does the Node match the CSS selector? */
        var proto = Element.prototype;
        var m = proto.matchesSelector || proto.webkitMatchesSelector ||
                proto.mozMatchesSelector;
        return m.call(node, selector);
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
    this.xhr.addEventListener('load', function() {
        callback(this.responseText);
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


$.log('autoCSP is in debug mode.', 'warn');
$.log('Request ID is ' + request_id + '.');


{% for script in scripts %}{{ script|safe }}{% endfor %}


})();