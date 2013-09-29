(function() {


var PREFIX = 'autoCSP';
var eventHandlers = null;
var inlineScripts = null;


(function() {
    // reset global state
    var $ = window.$;
    var $a = window.$a;
    var $n = window.$n;
    var $o = window.$o;
    var $s = window.$s;

    eventHandlers = { {% for e in events %}
        '{{ e.hash }}': function() { with(this) { {{ e.source|safe }} } },
    {% endfor %} };

    inlineScripts = { {% for s in sources %}
        '{{ s.hash }}': function() { {{ s.source|safe }} },
    {% endfor %} };
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
        var match = attr.nodeName.match(/^on([a-z]+$)/i);
        if (match) {
            var toBeHashed = match[1] + ',' + attr.nodeValue.trim();
            var hash = CryptoJS.SHA256(toBeHashed).toString();
            if ($o.in(eventHandlers, hash)) {
                var handler = eventHandlers[hash];
                handler = handler.bind(e);
                e[match[0]] = handler;
                if ($a.in(['load', 'error'], match[1])) {
                    // re-trigger events which could have already been fired
                    var prop = (e.tagName == 'LINK') ? 'href' : 'src';
                    var old = e[prop];
                    e[prop] = '';
                    e[prop] = old;
                }
            }
        }
    }
}


var executeInlineScript = function(e) {
    if (e.tagName !== 'SCRIPT') {
        return;
    }
    var hash = CryptoJS.SHA256(e.innerText.trim()).toString();
    if ($o.in(inlineScripts, hash)) {
        inlineScripts[hash]();
    }
};


window.addEventListener('DOMContentLoaded', function() {
    $a.forEach(document.getElementsByTagName('*'), function(e) {
        if (!e.tagName) {
            return;
        }
        addStyleAttrClass(e);
        addEventHandler(e);
        executeInlineScript(e);
    });

    var observer = new MutationObserver(function(mutations) {
        $a.forEach(mutations, function(mutation) {
            $a.forEach(mutation.addedNodes, function(node) {
                if (!node.tagName) {
                    return;
                }
                addStyleAttrClass(node);
                addEventHandler(node);
                executeInlineScript(e);
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