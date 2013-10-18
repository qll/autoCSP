(function() {
/** Policy generation script of autoCSP. */


// will contain a Map of Node types we want to visit
var visit = null;


var sanitizeUri = function(uri) {
    /** Nullifies data- and Same-Origin-URIs. */
    return ($.empty(uri) || $s.startsWith(uri, 'data:') ||
            $s.startsWith(uri, location.origin)) ? null : uri;
};


var xhrOpen = window.XMLHttpRequest.prototype.open;
var newOpen = function() {
    var uri = sanitizeUri(arguments[1]);
    if (uri) {
        $.sendToBackend({'connect-src': [uri]}, '{{ report_uri }}');
    }
    xhrOpen.apply(this, arguments);
};
Object.defineProperty(window.XMLHttpRequest.prototype, 'open',
                      {configurable: false, value: newOpen});


/** Contains all functions used to extract sources. **/
(function() {
    var getSrc = function(e) {
        return sanitizeUri(e.src);
    };
    var getBaseUri = function(e) {
        return sanitizeUri(e.href);
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
    var getFormAction = function(e) {
        return sanitizeUri(e.action);
    };
    var getButtonFormAction = function(e) {
        return sanitizeUri(e.formAction);
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
            if ($.empty(stylesheet.rules)) {
                return;
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
        'BASE': {'base-uri': getBaseUri},
        'BUTTON': {'form-action': getButtonFormAction},
        'EMBED': {'object-src': getSrc},
        'FORM': {'form-action': getFormAction},
        'FRAME': {'frame-src': getFrameSrc},
        'IFRAME': {'frame-src': getFrameSrc},
        'IMG': {'img-src': getSrc},
        'INPUT': {'form-action': getButtonFormAction},
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
    $.log('Policy.js: Start processing all nodes to infer rules...');
    var startTime = Date.now();

    var rules = $.processNodes(document.getElementsByTagName('*'), visit);
    $.sendToBackend(rules, '{{ report_uri }}');

    var delta = Date.now() - startTime;
    $.log('Policy.js: Finished processing all nodes in ' + delta + ' ms.');

    // register an observer for future changes (tree mod and attributes)
    var observer = new MutationObserver(function(mutations) {
        $a.forEach(mutations, function(mutation) {
            var nodes = (mutation.type === 'childList') ? mutation.addedNodes :
                                                          [mutation.target];
            var rules = $.processNodes(nodes, visit);
            $.sendToBackend(rules, '{{ report_uri }}');
        });
    });
    observer.observe(document.body.parentNode,
                     {subtree: true, childList: true, attributes: true});
});


})();