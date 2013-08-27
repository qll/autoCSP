// possibility #1
document.write('<img src="x" onerror="alert(1)">');


window.addEventListener('load', function() {
	// possibility #2
	document.body.innerHTML = '<img src="x" onerror="alert(2)">';

	// possiblity #3
	var img = document.createElement('img');
	img.onerror = function() { alert(3) };
	img.src = 'x';
	document.body.appendChild(img);
});