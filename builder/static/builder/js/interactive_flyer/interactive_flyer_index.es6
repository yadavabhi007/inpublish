App.interactive_flyer.index = {
    last_cropper_top: 0,
    last_cropper_left: 0,
    last_cropper_width: 0,
    last_cropper_height: 0,
    cropper_item: null,
    current_edit_index_link_id: null,

    init: function () {
        App.interactive_flyer.index.init_index_card();
    },

    open_create_modal: function () {
        $('#add-index-modal').modal('show');
    },

    init_index_card: function () {
        $(".index-card").click(function () {
            $(".page-card").removeClass("text-white bg-primary");
            $(this).addClass("text-white bg-primary");

            $("#flyer-pages-edit-container").hide();
            $("#flyer-index-edit-container").show();

            // App.edit_interactive_flyer.page_selected = $(this).data("number");
            App.interactive_flyer.index.load_page_canvas();
        });
    },

    load_page_canvas: function () {
        App.show_loader();
        $.ajax({
            method: "GET",
            url: "/load-index-canvas/" + App.edit_interactive_flyer.flyer_id
        })
            .done(function (data) {
                $("#center").html(data);
                $("#create-index-link-card").show();
                App.interactive_flyer.index.load_index_links();
            })
            .fail(function () {
                alert("Errore nel caricamento della pagina");
                App.hide_loader();
            })
            .always(function () {
                // App.hide_loader();
            });
    },

    load_index_links: function () {
        $.ajax({
            method: "GET",
            url: "/interactive-flyers/" + App.edit_interactive_flyer.flyer_id + "/index-links"
        })
            .done(function (data) {
                $("#index-links-container").html(data);
                // $("#page-number").html(App.edit_interactive_flyer.page_selected);
                // $("#page-products-card").show();
                App.hide_loader();
            })
            .fail(function () {
                alert("Spiacenti, si è verificato un errore nel caricamento dei prodotti interattivi della pagina");
                App.hide_loader();
            })
            .always(function () {
            });
        // App.hide_loader();
    },

    create_interactive_link: function () {
        App.show_loader();
        App.interactive_flyer.index.init_image_cropper(true);
        $("#create-index-link-card").hide();
        $("#new-index-link-card").show();
    },

    init_image_cropper: function (new_link) {
        var $image = $('.page-image');

        var data = null;
        var preview = null;
        var crop = null;

        if (!new_link) {
            data = {
                "x": parseFloat($("#edit-index-link-blueprint-left").val()),
                "y": parseFloat($("#edit-index-link-blueprint-top").val()),
                "height": parseFloat($("#edit-index-link-blueprint-height").val()),
                "width": parseFloat($("#edit-index-link-blueprint-width").val()),
                "rotate": 0,
                "scaleX": 1,
                "scaleY": 1
            }
            crop = function (event) {
                $("#index_link_blueprint_top_edit").val(event.detail.y);
                $("#index_link_blueprint_left_edit").val(event.detail.x);
                $("#index_link_blueprint_width_edit").val(event.detail.width);
                $("#index_link_blueprint_height_edit").val(event.detail.height);
            }
        } else if ((App.interactive_flyer.index.last_cropper_width > 0) && (App.interactive_flyer.index.last_cropper_height > 0)) {
            data = {
                "x": parseFloat(App.interactive_flyer.index.last_cropper_left),
                "y": parseFloat(App.interactive_flyer.index.last_cropper_top),
                "height": parseFloat(App.interactive_flyer.index.last_cropper_height),
                "width": parseFloat(App.interactive_flyer.index.last_cropper_width),
                "rotate": 0,
                "scaleX": 1,
                "scaleY": 1
            };
            crop = function (event) {
                $("#index_link_blueprint_top").val(event.detail.y);
                $("#index_link_blueprint_left").val(event.detail.x);
                $("#index_link_blueprint_width").val(event.detail.width);
                $("#index_link_blueprint_height").val(event.detail.height);
            }
        } else {
            crop = function (event) {
                $("#index_link_blueprint_top").val(event.detail.y);
                $("#index_link_blueprint_left").val(event.detail.x);
                $("#index_link_blueprint_width").val(event.detail.width);
                $("#index_link_blueprint_height").val(event.detail.height);
            }
        }

        $image.cropper({
            viewMode: 2,
            initialAspectRatio: 1,
            autoCropArea: 0.3,
            movable: false,
            zoomable: false,
            // preview: preview,
            data: data,
            crop: crop,
            ready: function (event) {
                App.hide_loader();
            }
        });

        App.interactive_flyer.index.cropper_item = $image;
    },

    cancel_index_link_creation: function () {
        App.interactive_flyer.index.reset_index_link_creation();
    },

    reset_index_link_creation: function () {
        $("#create-index-link-card").show();
        $("#new-index-link-card").hide();
        App.interactive_flyer.index.last_cropper_top = $("#index_link_blueprint_top").val();
        App.interactive_flyer.index.last_cropper_left = $("#index_link_blueprint_left").val();
        App.interactive_flyer.index.last_cropper_width = $("#index_link_blueprint_width").val();
        App.interactive_flyer.index.last_cropper_height = $("#index_link_blueprint_height").val();

        App.interactive_flyer.index.cropper_item.cropper("destroy");
    },

    save_index_link: function () {
        App.show_loader();
        $.ajax({
            method: "POST",
            url: "/interactive-flyers/" + App.edit_interactive_flyer.flyer_id + "/create-index-link",
            data: {
                page: $("#new-index-link-form_page").val(),
                blueprint_top: $("#index_link_blueprint_top").val(),
                blueprint_left: $("#index_link_blueprint_left").val(),
                blueprint_width: $("#index_link_blueprint_width").val(),
                blueprint_height: $("#index_link_blueprint_height").val()
            }
        })
            .done(function (data) {
                if (data.status == "created") {
                    App.interactive_flyer.index.reset_index_link_creation();
                    App.interactive_flyer.index.load_index_links();
                    App.show_feedback("success", "Link creato");
                }
            })
            .fail(function () {
                alert("Spiacenti, si è verificato un errore nella creazione del link sull'indice");
                App.hide_loader();
            })
            .always(function () {

            });
    },

    delete_index_link: function (link_id) {
        if (confirm("Sei sicuro di voler cancellare il link?")) {
            App.show_loader();
            $.ajax({
                method: "POST",
                url: "/interactive-flyers/" + App.edit_interactive_flyer.flyer_id + "/links/" + link_id + "/delete"
            })
                .done(function (data) {
                    if (data.status == "deleted") {
                        App.show_toast("Link eliminato");
                        App.interactive_flyer.index.load_index_links();
                    }
                })
                .fail(function () {
                    alert("Spiacenti, si è verificato un errore nella cancellazione del prodotto interattivo");
                })
                .always(function () {
                    App.hide_loader();
                });
        }
    },

    edit_index_link: function (link_id) {
        App.interactive_flyer.index.current_edit_index_link_id = link_id;
        App.show_loader();
        $.ajax({
            method: "GET",
            url: "/interactive-flyers/" + App.edit_interactive_flyer.flyer_id + "/links/" + App.interactive_flyer.index.current_edit_index_link_id + "/edit"
        })
            .done(function (data) {
                $("#edit-index-link-container").html(data);
                $("#create-index-link-card").hide();
                $("#index-links-container").hide();
                App.interactive_flyer.index.init_image_cropper(false);
                App.hide_loader();
            })
            .fail(function () {
                alert("Spiacenti, si è verificato un errore nel caricamento del link");
            });
    },

    cancel_index_link_edit: function () {
        App.interactive_flyer.index.reset_link_edit();
    },

    reset_link_edit: function () {
        $("#edit-index-link-container").empty();
        $("#create-index-link-card").show();
        $("#index-links-container").show();
        App.interactive_flyer.index.current_edit_index_link_id = null;

        App.interactive_flyer.index.cropper_item.cropper("destroy");
    },

    update_index_link: function () {
        App.show_loader();

        $.ajax({
            method: "POST",
            url: "/interactive-flyers/" + App.edit_interactive_flyer.flyer_id + "/links/" + App.interactive_flyer.index.current_edit_index_link_id + "/update",
            data: {
                page: $("#edit-index-link-form_page").val(),
                blueprint_top: $("#index_link_blueprint_top_edit").val(),
                blueprint_left: $("#index_link_blueprint_left_edit").val(),
                blueprint_width: $("#index_link_blueprint_width_edit").val(),
                blueprint_height: $("#index_link_blueprint_height_edit").val()
            }
        })
            .done(function (data) {
                if (data.status == "updated") {
                    App.interactive_flyer.index.reset_link_edit();
                    App.interactive_flyer.index.load_index_links();
                    App.show_toast("Link modificato");
                }
            })
            .fail(function () {
                alert("Spiacenti, si è verificato un errore durante l'aggiornamento del link");
                App.hide_loader();
            })
            .always(function () {
                
            });
    },
}