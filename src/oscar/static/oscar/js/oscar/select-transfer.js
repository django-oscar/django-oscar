(function($){

  var SelectBox = function(element, options) {
    var that = this;

    this.el = $(element);
    var el = this.el;

    this.filter_input = el.find('.selector-filter input');
    this.from_box = el.find('.selector-available select');
    this.to_box = el.find('.selector-chosen select');

    var findForm = function(node) {
        if (node.tagName.toLowerCase() != 'form') {
            return findForm(node.parentNode);
        }
        return node;
    }
    this.form = $(findForm(element));

    // link
    this.btn_add_all = el.find(".btn.selector-chooseall");
    this.btn_remove_all = el.find(".btn.selector-clearall");
    this.btn_add = el.find(".btn.selector-add");
    this.btn_remove = el.find(".btn.selector-remove");

    // setup event
    this.filter_input.keyup($.proxy(this.filter_key_up, this));
    this.filter_input.keydown($.proxy(this.filter_key_down, this));

    this.from_box.on('change', $.proxy(this.refresh_icons, this));
    this.to_box.on('change', $.proxy(this.refresh_icons, this));

    this.from_box.on('dblclick', $.proxy(this.move, this));
    this.to_box.on('dblclick', $.proxy(this.remove, this));

    this.btn_add.on('click', $.proxy(this.move, this));
    this.btn_remove.on('click', $.proxy(this.remove, this));

    this.btn_add_all.on('click', $.proxy(this.move_all, this));
    this.btn_remove_all.on('click', $.proxy(this.remove_all, this));

    this.form.submit($.proxy(this.select_all, this));

    // init cache
    var from_cache = new Array();
    for (var i = 0; (node = this.from_box[0].options[i]); i++) {
      from_cache.push({value: node.value, text: node.text, displayed: 1});
    }
    this.from_box.data('cache', from_cache);

    var to_cache = new Array();
    for (var i = 0; (node = this.to_box[0].options[i]); i++) {
      to_cache.push({value: node.value, text: node.text, displayed: 1});
    }
    this.to_box.data('cache', to_cache);

    this.refresh_icons();
  }

  SelectBox.prototype = {
    constructor: SelectBox,
    redisplay : function(box){
      var select = box[0];
      var cache = box.data('cache');
      select.options.length = 0; // clear all options
      for (var i = 0, j = cache.length; i < j; i++) {
          var node = cache[i];
          if (node.displayed) {
              select.options[select.options.length] = new Option(node.text, node.value, false, false);
          }
      }
    },
    filter: function(text) {
      // Redisplay the HTML select box, displaying only the choices containing ALL
      // the words in text. (It's an AND search.)
      var tokens = text.toLowerCase().split(/\s+/);
      var node, token;
      for (var i = 0; (node = this.from_box.data('cache')[i]); i++) {
          node.displayed = 1;
          for (var j = 0; (token = tokens[j]); j++) {
              if (node.text.toLowerCase().indexOf(token) == -1) {
                  node.displayed = 0;
              }
          }
      }
      this.redisplay(this.from_box);
    },
    remove: function(){
      this.trans(this.to_box, this.from_box);
    },
    move: function(){
      this.trans(this.from_box, this.to_box);
    },
    delete_from_cache: function(box, value) {
        var node, delete_index = null;
        var cache = box.data('cache');
        for (var i = 0; (node = cache[i]); i++) {
            if (node.value == value) {
                delete_index = i;
                break;
            }
        }
        var j = cache.length - 1;
        for (var i = delete_index; i < j; i++) {
            cache[i] = cache[i+1];
        }
        cache.length--;
    },
    add_to_cache: function(box, option) {
        box.data('cache').push({value: option.value, text: option.text, displayed: 1});
    },
    cache_contains: function(box, value) {
        // Check if an item is contained in the cache
        var node;
        for (var i = 0; (node = box.data('cache')[i]); i++) {
            if (node.value == value) {
                return true;
            }
        }
        return false;
    },
    trans: function(from, to){
      for (var i = 0; (option = from[0].options[i]); i++) {
          if (option.selected && this.cache_contains(from, option.value)) {
              this.add_to_cache(to, {value: option.value, text: option.text, displayed: 1});
              this.delete_from_cache(from, option.value);
          }
      }
      this.redisplay(from);
      this.redisplay(to);

      this.refresh_icons();
    },
    move_all : function(){
      this.trans_all(this.from_box, this.to_box);
    },
    remove_all: function(){
      this.trans_all(this.to_box, this.from_box);
    },
    trans_all: function(from, to) {
      var option;
      for (var i = 0; (option = from[0].options[i]); i++) {
          if (this.cache_contains(from, option.value)) {
              this.add_to_cache(to, {value: option.value, text: option.text, displayed: 1});
              this.delete_from_cache(from, option.value);
          }
      }
      this.redisplay(from);
      this.redisplay(to);

      this.refresh_icons();
    },
    sort: function(box) {
        box.data('cache').sort( function(a, b) {
            a = a.text.toLowerCase();
            b = b.text.toLowerCase();
            try {
                if (a > b) return 1;
                if (a < b) return -1;
            }
            catch (e) {
                // silently fail on IE 'unknown' exception
            }
            return 0;
        } );
    },
    select_all: function() {
        var box = this.to_box[0];
        for (var i = 0; i < box.options.length; i++) {
            box.options[i].selected = 'selected';
        }
    },
    refresh_icons: function() {
        var is_from_selected = this.from_box.find('option:selected').length > 0;
        var is_to_selected = this.to_box.find('option:selected').length > 0;
        // Active if at least one item is selected
        this.btn_add.toggleClass('disabled', !is_from_selected);
        this.btn_remove.toggleClass('disabled', !is_to_selected);
        // Active if the corresponding box isn't empty
        this.btn_add_all.toggleClass('disabled', this.from_box.find('option').length == 0);
        this.btn_remove_all.toggleClass('disabled', this.to_box.find('option').length == 0);
    },
    filter_key_up: function(event) {
      var from = this.from_box[0];
      // don't submit form if user pressed Enter
      if ((event.which && event.which == 13) || (event.keyCode && event.keyCode == 13)) {
        var temp = from.selectedIndex;
        this.move();
        from.selectedIndex = temp;
        return false;
      }
      var temp = from.selectedIndex;
      this.filter(this.filter_input.val());
      from.selectedIndex = temp;
      return true;
    },
    filter_key_down: function(event) {
      var from = this.from_box[0];
      if ((event.which && event.which == 13) || (event.keyCode && event.keyCode == 13)) {
        return false;
      }
      // right arrow -- move across
      if ((event.which && event.which == 39) || (event.keyCode && event.keyCode == 39)) {
          var old_index = from.selectedIndex;
          this.move();
          from.selectedIndex = (old_index == from.length) ? from.length - 1 : old_index;
          return false;
      }
      // down arrow -- wrap around
      if ((event.which && event.which == 40) || (event.keyCode && event.keyCode == 40)) {
          from.selectedIndex = (from.length == from.selectedIndex + 1) ? 0 : from.selectedIndex + 1;
      }
      // up arrow -- wrap around
      if ((event.which && event.which == 38) || (event.keyCode && event.keyCode == 38)) {
          from.selectedIndex = (from.selectedIndex == 0) ? from.length - 1 : from.selectedIndex - 1;
      }
      return true;
    }

  }

  $.fn.select_transfer = function ( option ) {
    var args = Array.apply(null, arguments);
    args.shift();
    return this.each(function () {
      var $this = $(this),
        data = $this.data('transfer'),
        options = typeof option == 'object' && option;
      if (!data) {
        $this.data('transfer', (data = new SelectBox(this)));
      }
    });
  };

})(jQuery);
