App.dashboard = {
    interactive_flyers: [],

    init: function () {
        App.show_loader($("#interactive-flyer-list"));
        App.dashboard.load_interactive_flyers();
    },

    load_interactive_flyers: function () {
        $.ajax({
            method: "GET",
            url: "/interactive-flyers"
        })
            .done(function (data) {
                App.dashboard.interactive_flyers = data;
                App.dashboard.init_interactive_flyers_table();
            })
            .fail(function () {
                alert("error");
            })
            .always(function () {
                App.hide_loader($("#interactive-flyer-list"));
            });
    },

    init_interactive_flyers_table: function(){
        $('#interactive-flyer-table').DataTable({
            data: App.dashboard.interactive_flyers,
            columns: [
              { data: 'name' },
              {
                data: null,
                render: function (data, type, row) {
                  return '<a class="btn btn-secondary btn-sm" href="/edit-interactive-flyer/' + row.id + '">Edit</a>';
                }
              }
            ]
          });
    }
}