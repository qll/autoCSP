(function() {
    var csrf_token = document.querySelector('*[data-csrf]').dataset.csrf;
    var path = location.pathname.slice(0, -('policy'.length)) + 'rule/active';

    var changeActive = function(id, active) {
        var xhr = new XMLHttpRequest();
        xhr.addEventListener('load', function() {
            csrf_token = xhr.responseText;
        });
        xhr.open('POST', path);
        xhr.setRequestHeader('Content-Type',
                             'application/x-www-form-urlencoded');
        xhr.send('id=' + encodeURIComponent(id) + '&active=' +
                 encodeURIComponent(active) + '&csrf=' +
                 encodeURIComponent(csrf_token));
    };

    var nodes = document.querySelectorAll('.chk-active');
    Array.prototype.forEach.call(nodes, function(e) {
        e.addEventListener('change', function() {
            if (this.checked) {
                this.parentNode.parentNode.classList.remove('inactive');
            } else {
                this.parentNode.parentNode.classList.add('inactive');
            }
            changeActive(this.dataset.id, this.checked ? 1 : 0);
        });
    });
    
})();