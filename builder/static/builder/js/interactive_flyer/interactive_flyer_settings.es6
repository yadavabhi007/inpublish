App.interactive_flyer.settings = {
    selected_seller_id: null,

    init: function(){
        App.interactive_flyer.settings.init_seller_select();
        App.interactive_flyer.settings.init_project_select();
    },

    init_seller_select: function () {
        // $('#seller-select').select2({
        //     theme: "bootstrap4",
        //     placeholder: 'Seleziona un cliente'
        // });

        $('#seller-select').change(function () {
            App.show_loader($("#affiliate-container"));
            App.show_loader($("#project-container"));
            App.interactive_flyer.settings.selected_seller_id = $(this).val();
            App.interactive_flyer.settings.load_seller_affiliates_select();
            App.interactive_flyer.settings.load_seller_projects_select();
        });
    },

    init_project_select: function () {
        // $('#project-select').select2({
        //     theme: "bootstrap4",
        //     placeholder: 'Seleziona progetti',
        //     multiple: true,
        // });
    },

    load_seller_affiliates_select: function () {
        $.ajax({
            method: "GET",
            url: "/seller-affiliates-select",
            data: {
                seller_id: App.interactive_flyer.settings.selected_seller_id
            }
        })
            .done(function (data) {
                $("#affiliate-select-container").html(data);
            })
            .fail(function () {
                alert("error");
            })
            .always(function () {
                App.hide_loader($("#affiliate-container"));
            });
    },

    load_seller_projects_select: function () {
        $.ajax({
            method: "GET",
            url: "/seller-projects-select",
            data: {
                seller_id: App.interactive_flyer.settings.selected_seller_id
            }
        })
            .done(function (data) {
                $("#project-select-container").html(data);
            })
            .fail(function () {
                alert("error");
            })
            .always(function () {
                App.hide_loader($("#project-container"));
            });
    }
}