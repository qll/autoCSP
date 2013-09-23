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
            var match = attr.nodeName.match(/on([a-z]+)/i);
            if (match && !$.empty(attr.nodeValue.trim())) {
                eventHandlers.push(match[1] + ',' + attr.nodeValue.trim());
            }
        }
        return eventHandlers;
    };

    visit = {
        '*': {'css-attr': getStyleAttribute, 'js-event': getEventHandlers},
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
        if (attr === 'style') {
            externalize([this]);
        }
    };
    Object.defineProperty(Element.prototype, 'setAttribute',
                          {value: setAttributeReplacement});
});


})();