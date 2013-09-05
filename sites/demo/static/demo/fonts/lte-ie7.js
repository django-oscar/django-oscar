/* Load this script using conditional IE comments if you need to support IE 7 and IE 6. */

window.onload = function() {
	function addIcon(el, entity) {
		var html = el.innerHTML;
		el.innerHTML = '<span style="font-family: \'icomoon\'">' + entity + '</span>' + html;
	}
	var icons = {
			'icon-cart' : '&#xe000;',
			'icon-star' : '&#xe001;',
			'icon-lock' : '&#xf0be;',
			'icon-mobile' : '&#xe002;',
			'icon-earth' : '&#xe003;',
			'icon-arrow-right' : '&#xe004;',
			'icon-search' : '&#xf0c5;',
			'icon-truck' : '&#xf211;',
			'icon-twitter' : '&#xe005;',
			'icon-facebook' : '&#xe006;',
			'icon-pinterest' : '&#xe007;',
			'icon-mail' : '&#xe008;',
			'icon-plus' : '&#x2b;',
			'icon-noun_project_62' : '&#x21;',
			'icon-arrow-down' : '&#x22;',
			'icon-check-alt' : '&#x23;',
			'icon-x-altx-alt' : '&#x24;',
			'icon-checkout-half-wheel' : '&#x25;'
		},
		els = document.getElementsByTagName('*'),
		i, attr, html, c, el;
	for (i = 0; ; i += 1) {
		el = els[i];
		if(!el) {
			break;
		}
		attr = el.getAttribute('data-icon');
		if (attr) {
			addIcon(el, attr);
		}
		c = el.className;
		c = c.match(/icon-[^\s'"]+/);
		if (c && icons[c[0]]) {
			addIcon(el, icons[c[0]]);
		}
	}
};