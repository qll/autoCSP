(function() {

window.addEventListener('DOMContentLoaded', function() {
    var addStyleAttrClass = function(node) {
        /** Assign class to all Elements with inline style attributes. */
        var code = node.getAttribute('style').trim();
        var hash = CryptoJS.SHA256(code).toString();
        node.classList.add('autoCSP' + hash);
    }
    $a.forEach(document.querySelectorAll('*[style]'), addStyleAttrClass);
    var observer = new MutationObserver(function(mutations) {
        $a.forEach(mutations, function(mutation) {
            $a.forEach(mutation.addedNodes, function(node) {
                if (node.tagName && node.hasAttribute('style')) {
                    addStyleAttrClass(node);
                }
            });
        });
    });
    observer.observe(document.body.parentNode,
                     {subtree: true, childList: true});

    var setAttribute = Element.prototype.setAttribute;
    var setAttributeReplacement = function(attr, value) {
        setAttribute.call(this, attr, value);
        if (attr === 'style') {
            addStyleAttrClass(this);
        }
    };
    Object.defineProperty(Element.prototype, 'setAttribute',
                          {value: setAttributeReplacement});
});

})();