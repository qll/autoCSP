(function() {
/** Inline script and style externalizer. */


var visit = null;


(function() {
    var getStyleAttribute = function(e) {
        if (e.hasAttribute('style')) {
            return e.getAttribute('style').trim();
        }
    };
    var getEventHandlers = function(e) {
        var eventHandlers = [];
        for (var i = 0; i < e.attributes.length; i++) {
            var attr = e.attributes.item(i);
            var match = attr.nodeName.match(/^on([a-z]+$)/i);
            if (match && !$.empty(attr.nodeValue.trim())) {
                var handler = [match[1], $.getNodePath(e),
                               attr.nodeValue.trim()];
                eventHandlers.push(handler.join(','));
            }
        }
        return eventHandlers;
    };
    var getJsLink = function(e) {
        var uri = e.href;
        if ($s.startsWith(uri, 'javascript:')) {
            return $.getNodePath(e) + ',' + uri.slice('javascript:'.length);
        }
    };
    var getInlineScript = function(e) {
        if (!e.hasAttribute('src')) {
            return e.innerText.trim();
        }
    };

    visit = {
        '*': {'css-attr': getStyleAttribute, 'js-event': getEventHandlers},
        'A': {'js-link': getJsLink},
        'SCRIPT': {'js': getInlineScript},
        'STYLE': {'css': function(e) { return e.innerText.trim(); }},
    };
})();


window.addEventListener('load', function() {
    var knownHashes = [{{ known_hashes|join(',')|safe }}];
    var check = function(value) {
        /** Don't resend known hashes. */
        var hash = CryptoJS.SHA256(value).toString();
        if ($a.in(knownHashes, hash)) {
            return false;
        }
        return true;
    };
    var externalize = function(nodes) {
        var inline = $.processNodes(nodes, visit, check);
        $.sendToBackend(inline, '{{ externalizer_uri }}');
    };

    $.log('Externalize.js: Start externalizing all inline code.');
    var startTime = Date.now();
    externalize(document.getElementsByTagName('*'));
    var delta = Date.now() - startTime;
    $.log('Externalize.js: Finished externalizing code in ' + delta + ' ms.');

    // register an observer for future changes (tree mod and attributes)
    var observer = new MutationObserver(function(mutations) {
        $a.forEach(mutations, function(mutation) {
            externalize(mutation.addedNodes);
        });
    });
    observer.observe(document.body.parentNode,
                     {subtree: true, childList: true});

    var setAttribute = Element.prototype.setAttribute;
    var setAttributeReplacement = function(attr, value) {
        setAttribute.call(this, attr, value);
        if (attr === 'style' || attr.match(/^on[a-z]+$/i)) {
            externalize([this]);
        }
    };
    Object.defineProperty(Element.prototype, 'setAttribute',
                          {value: setAttributeReplacement});
});


})();