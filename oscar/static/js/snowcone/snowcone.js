//Script to ensure Snowcone will work for legacy browsers, that don't support the :before pseudo class

function addicons(){
	//Create object with list of icons
		var icons = {
		  ico_alert: "A",
		  ico_cross: "B" || outofstock: "B",
		  ico_tick: "C" || instock: "C",
			ico_expand: "D",
			ico_contract: "E",
			ico_view: "F",
			ico_sync: "G",
			ico_home: "H",
			ico_outline_down: "I",
			ico_outline_up: "J",
			ico_outline_right: "K",
			ico_outline_left: "L",
			ico_stop: "M",
			ico_mapmarker: "N",
			ico_favourite: "O",
			ico_profile: "P",
			ico_magnify: "Q",
			ico_comment: "R",
			ico_settings: "S",
			ico_edit: "T",
			ico_email: "U",
			ico_shop_bag: "V",
			ico_logout: "W", 
			ico_heart: "X", 
			ico_rss: "Z", 
			ico_link: "a", 
			ico_fill_down: "b", 
			ico_fill_up: "c", 
			ico_fill_right: "d", 
			ico_fill_left: "e", 
			ico_facebook: "f", 
			ico_twitter: "g", 
			ico_googleplus: "h", 
			ico_blacklist: "i", 
			ico_twitter_bird: "t", 
			ico_twitter_plain: "u", 
			ico_tag: "t", 
			ico_speedo: "y",  
			ico_tangentsnowball: "z"
		};
	//Detect IE version	
		var browserver = parseInt($.browser.version, 10)
	
	//Run icon insertion	
		if ($.browser.msie && browserver == 6 || browserver == 7){
			$(".app-ico").each(function(){
				var icon = $(this).attr("class").split(/\s/);
				for(key in icons){
					if([key]==icon[1]){
						$(this).prepend("<span class='app-legacy_ico'>" + icons[key] + "</span>");
					};
				}
			});
		}
}

//Run function
	$(document).ready(function(){
		addicons();
	});
	
