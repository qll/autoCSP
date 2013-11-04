(function() {


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
        '{{ s.hash }}': {{ s.id }},
    {% endfor %} };

    jsLinks = { {% for l in links %}
        '{{ l.hash }}': function() { {{ l.source|safe }} },
    {% endfor %} };
})();


var PREFIX = 'autoCSP';
var visit = null;


(function() {
    var executeInlineScript = function(e) {
        var hash = CryptoJS.SHA256(e.innerText.trim()).toString();
        if ($o.in(inlineScripts, hash)) {
            var script = document.createElement('script');
            script.src = '{{ extjs_uri }}?id=' + inlineScripts[hash];
            document.body.appendChild(script);
        }
    };
    var addEventHandler = function(e) {
        /** Assign class to all Elements with inline event handlers. */
        for (var i = 0; i < e.attributes.length; i++) {
            var attr = e.attributes.item(i);
            var match = attr.nodeName.match(/^on([a-z]+$)/i);
            if (match) {
                var handlerProps = [match[1], $.getNodePath(e),
                                    attr.nodeValue.trim()];
                var hash = CryptoJS.SHA256(handlerProps.join(',')).toString();
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
    };
    var addClickEvent = function(e) {
        var prot = 'javascript:';
        if ($s.startsWith(e.href, prot)) {
            var hashProperties = [$.getNodePath(e), e.href.slice(prot.length)];
            var hash = CryptoJS.SHA256(hashProperties.join(',')).toString();
            if ($o.in(jsLinks, hash)) {
                var handler = jsLinks[hash];
                e.onclick = handler;
            }
        }
    };
    var addStyleAttrClass = function(e) {
        /** Assign class to all Elements with inline style attributes. */
        if (!e.hasAttribute('style')) {
            return;
        }
        var hash = CryptoJS.SHA256(e.getAttribute('style').trim()).toString();
        e.classList.add(PREFIX + hash);
    };

    visit = {
        '*': {'js-event': addEventHandler, 'css-attr': addStyleAttrClass},
        'A': {'js-link': addClickEvent},
        'SCRIPT': {'js': executeInlineScript},
    };
})();


window.addEventListener('DOMContentLoaded', function() {
    var caller = function(_, externalizer, node) {
        externalizer(node);
    };
    $.visitNodes(document.getElementsByTagName('*'), visit, caller);

    var observer = new MutationObserver(function(mutations) {
        $a.forEach(mutations, function(mutation) {
            $.visitNodes(mutation.addedNodes, visit, caller);
        });
    });
    observer.observe(document.body.parentNode,
                     {subtree: true, childList: true});

    var setAttribute = Element.prototype.setAttribute;
    var setAttributeReplacement = function(attr, value) {
        setAttribute.call(this, attr, value);
        var node = this;
        $a.forEach(visit['*'], function(func) {
            func(this);
        });
    };
    Object.defineProperty(Element.prototype, 'setAttribute',
                          {value: setAttributeReplacement});
});

})();