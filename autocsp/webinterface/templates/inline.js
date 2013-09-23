(function() {


var PREFIX = 'autoCSP';
var JSPREFIX = 'autoCSPjs';
var eventHandlers = null;


(function() {
    // reset global state
    var $ = window.$;
    var $a = window.$a;
    var $n = window.$n;
    var $o = window.$o;
    var $s = window.$s;

    eventHandlers = {
    {% for e in events %}
        '{{ e.hash }}': function() { {{ e.source }} },
    {% endfor %}
    };
})();


var addStyleAttrClass = function(node) {
    /** Assign class to all Elements with inline style attributes. */
    if (!node.hasAttribute('style')) {
        return;
    }
    var hash = CryptoJS.SHA256(node.getAttribute('style').trim()).toString();
    node.classList.add(PREFIX + hash);
}


var addEventHandler = function(e) {
    /** Assign class to all Elements with inline event handlers. */
    for (var i = 0; i < e.attributes.length; i++) {
        var attr = e.attributes.item(i);
        var match = attr.nodeName.match(/on([a-z]+)/i);
        if (match) {
            var toBeHashed = match[1] + ',' + attr.nodeValue.trim();
            var hash = CryptoJS.SHA256(toBeHashed).toString();
            if ($o.in(eventHandlers, hash)) {
                e.removeAttribute(match[0]);
                e.classList.add(JSPREFIX + hash);
                e[match[0]] = eventHandlers[hash];
            }
        }
    }
}


window.addEventListener('DOMContentLoaded', function() {
    $a.forEach(document.getElementsByTagName('*'), function(e) {
        if (!e.tagName) {
            return;
        }
        addStyleAttrClass(e);
        addEventHandler(e);
    });

    var observer = new MutationObserver(function(mutations) {
        $a.forEach(mutations, function(mutation) {
            $a.forEach(mutation.addedNodes, function(node) {
                if (!node.tagName) {
                    return;
                }
                addStyleAttrClass(node);
                addEventHandler(node);
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
        } else if (attr.match(/^on[a-z]+$/i)) {
            addEventHandler(this);
        }
    };
    Object.defineProperty(Element.prototype, 'setAttribute',
                          {value: setAttributeReplacement});
});

})();