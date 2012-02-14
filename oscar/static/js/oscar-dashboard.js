// oscar-dashboard.js

var oscar = oscar || {}
oscar.dashboard = {
    promotions: {
        init: function() {
            $('.promotion_list').sortable({
                handle: '.btn-handle',
                stop: oscar.dashboard.promotions.save_order});
        },
        save_order: function(event, ui) {
            // todo - save order of promotions
            console.log(event, ui);
        }
    }
}
