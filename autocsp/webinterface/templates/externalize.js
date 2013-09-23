(function() {
/** Inline script and style externalizer. */


var visit = null;


(function() {
    var getStyleAttribute = function(e) {
        if (e.hasAttribute('style')) {
            return e.getAttribute('style').trim();
        }
    };

    visit = {
        '*': {'css-attr': getStyleAttribute},
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

    $.log('Externalize.js: Start processing all nodes to infer rules...');
    var startTime = Date.now();

    var inline = $.processNodes(document.getElementsByTagName('*'), visit,
                                check);
    $.sendToBackend(inline, '{{ externalizer_uri }}');

    var delta = Date.now() - startTime;
    $.log('Externalize.js: Finished processing all nodes in ' + delta + ' ms.');

    // register an observer for future changes (tree mod and attributes)
    var observer = new MutationObserver(function(mutations) {
        $a.forEach(mutations, function(mutation) {
            var nodes = (mutation.type === 'childList') ? mutation.addedNodes :
                                                          [mutation.target];
            var inline = $.processNodes(nodes, visit);
            $.sendToBackend(inline, '{{ externalizer_uri }}');
        });
    });
    observer.observe(document.body.parentNode,
                     {subtree: true, childList: true});
});


})();