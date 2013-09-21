(function() {

window.addEventListener('DOMContentLoaded', function() {
    /** Assign class to all Elements with inline style attributes. */
    $a.forEach(document.querySelectorAll('*[style]'), function(node) {
        var code = node.getAttribute('style').trim();
        var hash = CryptoJS.SHA256(code).toString();
        node.classList.add('autoCSP' + hash);
    });
});

})();