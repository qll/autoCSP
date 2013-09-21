(function() {
/** Inline script and style externalizer. */

var knownHashes = [{{ known_hashes|join(',')|safe }}];
var selectors = {
    'style': ['css', function(e) { return e.innerText; }],
    '*[style]': ['css-attr', function(e) { return e.getAttribute('style'); }]
};


window.addEventListener('load', function() {
    var inlineCode = {};
    $o.forEach(selectors, function(selector, value) {
        var type = value[0];
        var getter = value[1];
        $a.forEach(document.querySelectorAll(selector), function(e) {
            var code = getter(e).trim();
            if ($.empty(code)) {
                return;
            }
            var hash = CryptoJS.SHA256(code).toString();
            if (!$a.in(knownHashes, hash)) {
                $o.setDefault(inlineCode, type, []).push(code)
            }
        });
    });
    if (!$.empty(inlineCode)) {
        var inline = JSON.stringify(inlineCode);
        $.log('Externalize.js: Sending data to backend for ' + document_uri +
              ':\n' + inline)
        $n.post('{{ externalizer_uri }}', {'id': request_id, 'inline': inline,
                                           'uri': document_uri});
    }
});


})();