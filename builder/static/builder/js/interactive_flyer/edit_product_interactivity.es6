App.edit_product_interactivity = {
    interactivity_present_badge: '<span class="badge badge-success">presente</span>',
    interactivity_not_present_badge: '<span class="badge badge-secondary">non presente</span>',

    load_edit_link_interactivity_modal: function () {
        App.show_loader();
        $.ajax({
            method: "GET",
            url: "/interactive-flyers/" + App.edit_interactive_flyer.flyer_id + "/products/" + App.edit_interactive_flyer.current_edit_interactive_product_id + "/interactivities/link/edit"
        })
            .done(function (data) {
                $("#edit-link-interactivity-modal-container").html(data);
                $("#link-interactivity-modal").modal("show");
            })
            .fail(function () {
                alert("load_edit_link_interactivity_modal error");
            })
            .always(function () {
                App.hide_loader();
            });
    },

    save_link_interactivity: function () {
        App.show_loader();
        data = {
            link: $("#edit-link-interactivity_link").val(),
            title: $("#edit-link-interactivity_title").val()
        }
        if ($("#edit-link-interactivity_active").prop('checked')) {
            data.active = "true";
        }
        $.ajax({
            method: "POST",
            url: "/interactive-flyers/" + App.edit_interactive_flyer.flyer_id + "/products/" + App.edit_interactive_flyer.current_edit_interactive_product_id + "/interactivities/link/update",
            data: data
        })
            .done(function (data) {
                $("#link-interactivity-modal").modal("hide");
                $("#link-interactivity-badge-container").html(data.active ? App.edit_product_interactivity.interactivity_present_badge : App.edit_product_interactivity.interactivity_not_present_badge);

                if (App.edit_interactive_flyer.page_selected != null) {
                    $.ajax({
                        method: "GET",
                        url: "/interactive-flyer/" + App.edit_interactive_flyer.flyer_id + "/products",
                        data: {
                            page_number: App.edit_interactive_flyer.page_selected
                        }
                    })
                        .done(function (data) {
                            $("#page-products-container").html(data);
                        })
                        .fail(function () {
                            alert("Spiacenti, si è verificato un errore nel caricamento dei prodotti interattivi della pagina");
                        })
                        .always(function () {
                            App.hide_loader();
                        });
                }
                else {
                    App.hide_loader();
                    App.edit_iflyer_wpag.load_products();
                }

            })
            .fail(function () {
                App.hide_loader();
                alert("save_link_interactivity error");
            })
            .always(function () {
            });
    },

    load_edit_video_interactivity_modal: function () {
        App.show_loader();
        $.ajax({
            method: "GET",
            url: "/interactive-flyers/" + App.edit_interactive_flyer.flyer_id + "/products/" + App.edit_interactive_flyer.current_edit_interactive_product_id + "/interactivities/video/edit"
        })
            .done(function (data) {
                $("#edit-video-interactivity-modal-container").html(data);
                $("#video-interactivity-modal").modal("show");
            })
            .fail(function () {
                alert("load_edit_video_interactivity_modal error");
            })
            .always(function () {
                App.hide_loader();
            });
    },

    save_video_interactivity: function () {
        App.show_loader();

        var form_data = new FormData();

        if ($("#edit-video-interactivity_video_file")[0].files) {
            var video_file_data = $("#edit-video-interactivity_video_file")[0].files[0];
            form_data.append("video_file", video_file_data);
        }
        form_data.append("title", $("#edit-video-interactivity_title").val());
        if ($("#edit-video-interactivity_active").prop('checked')) {
            form_data.append("active", "true");
        }
        $.ajax({
            method: "POST",
            url: "/interactive-flyers/" + App.edit_interactive_flyer.flyer_id + "/products/" + App.edit_interactive_flyer.current_edit_interactive_product_id + "/interactivities/video/update",
            contentType: false,
            processData: false,
            data: form_data
        })
            .done(function (data) {
                $("#video-interactivity-modal").modal("hide");
                $("#video-interactivity-badge-container").html(data.active ? App.edit_product_interactivity.interactivity_present_badge : App.edit_product_interactivity.interactivity_not_present_badge);

                if (App.edit_interactive_flyer.page_selected != null) {
                    $.ajax({
                        method: "GET",
                        url: "/interactive-flyer/" + App.edit_interactive_flyer.flyer_id + "/products",
                        data: {
                            page_number: App.edit_interactive_flyer.page_selected
                        }
                    })
                        .done(function (data) {
                            $("#page-products-container").html(data);
                        })
                        .fail(function () {
                            alert("Spiacenti, si è verificato un errore nel caricamento dei prodotti interattivi della pagina");
                        })
                        .always(function () {
                            App.hide_loader();
                        });
                }
                else {
                    App.hide_loader();
                    App.edit_iflyer_wpag.load_products();
                }
            })
            .fail(function () {
                App.hide_loader();
                alert("save_video_interactivity error");
            })
            .always(function () {
            });
    },

    load_edit_recipe_interactivity_modal: function () {
        App.show_loader();
        $.ajax({
            method: "GET",
            url: "/interactive-flyers/" + App.edit_interactive_flyer.flyer_id + "/products/" + App.edit_interactive_flyer.current_edit_interactive_product_id + "/interactivities/recipe/edit"
        })
            .done(function (data) {
                $("#edit-recipe-interactivity-modal-container").html(data);
                $("#recipe-interactivity-modal").modal("show");
            })
            .fail(function () {
                alert("load_edit_recipe_interactivity_modal error");
            })
            .always(function () {
                App.hide_loader();
            });
    },

    save_recipe_interactivity: function () {
        App.show_loader();

        var form_data = new FormData();

        if ($("#edit-recipe-interactivity_image_file")[0].files) {
            var image_file_data = $("#edit-recipe-interactivity_image_file")[0].files[0];
            form_data.append("image_file", image_file_data);
        }
        form_data.append("title", $("#edit-recipe-interactivity_title").val());
        form_data.append("ingredients", $("#edit-recipe-interactivity_ingredients").val());
        form_data.append("recipe", $("#edit-recipe-interactivity_recipe").val());
        if ($("#edit-recipe-interactivity_active").prop('checked')) {
            form_data.append("active", "true");
        }
        $.ajax({
            method: "POST",
            url: "/interactive-flyers/" + App.edit_interactive_flyer.flyer_id + "/products/" + App.edit_interactive_flyer.current_edit_interactive_product_id + "/interactivities/recipe/update",
            contentType: false,
            processData: false,
            data: form_data
        })
            .done(function (data) {
                $("#recipe-interactivity-modal").modal("hide");
                $("#recipe-interactivity-badge-container").html(data.active ? App.edit_product_interactivity.interactivity_present_badge : App.edit_product_interactivity.interactivity_not_present_badge);

                if (App.edit_interactive_flyer.page_selected != null) {
                    $.ajax({
                        method: "GET",
                        url: "/interactive-flyer/" + App.edit_interactive_flyer.flyer_id + "/products",
                        data: {
                            page_number: App.edit_interactive_flyer.page_selected
                        }
                    })
                        .done(function (data) {
                            $("#page-products-container").html(data);
                        })
                        .fail(function () {
                            alert("Spiacenti, si è verificato un errore nel caricamento dei prodotti interattivi della pagina");
                        })
                        .always(function () {
                            App.hide_loader();
                        });
                }
                else {
                    App.hide_loader();
                    App.edit_iflyer_wpag.load_products();
                }
            })
            .fail(function () {
                App.hide_loader();
                alert("save_recipe_interactivity error");
            })
            .always(function () {
            });
    },

    load_edit_info_interactivity_modal: function () {
        App.show_loader();
        $.ajax({
            method: "GET",
            url: "/interactive-flyers/" + App.edit_interactive_flyer.flyer_id + "/products/" + App.edit_interactive_flyer.current_edit_interactive_product_id + "/interactivities/info/edit"
        })
            .done(function (data) {
                $("#edit-info-interactivity-modal-container").html(data);
                $("#info-interactivity-modal").modal("show");
            })
            .fail(function () {
                alert("load_info_recipe_interactivity_modal error");
            })
            .always(function () {
                App.hide_loader();
            });
    },

    save_info_interactivity: function () {
        App.show_loader();

        var form_data = new FormData();

        if ($("#edit-info-interactivity_image_file")[0].files) {
            var image_file_data = $("#edit-info-interactivity_image_file")[0].files[0];
            form_data.append("image_file", image_file_data);
        }
        form_data.append("title", $("#edit-info-interactivity_title").val());
        form_data.append("content_title", $("#edit-info-interactivity_content-title").val());
        form_data.append("content_text", $("#edit-info-interactivity_content-text").val());
        if ($("#edit-info-interactivity_active").prop('checked')) {
            form_data.append("active", "true");
        }
        $.ajax({
            method: "POST",
            url: "/interactive-flyers/" + App.edit_interactive_flyer.flyer_id + "/products/" + App.edit_interactive_flyer.current_edit_interactive_product_id + "/interactivities/info/update",
            contentType: false,
            processData: false,
            data: form_data
        })
            .done(function (data) {
                $("#info-interactivity-modal").modal("hide");
                $("#info-interactivity-badge-container").html(data.active ? App.edit_product_interactivity.interactivity_present_badge : App.edit_product_interactivity.interactivity_not_present_badge);

                if (App.edit_interactive_flyer.page_selected != null) {
                    $.ajax({
                        method: "GET",
                        url: "/interactive-flyer/" + App.edit_interactive_flyer.flyer_id + "/products",
                        data: {
                            page_number: App.edit_interactive_flyer.page_selected
                        }
                    })
                        .done(function (data) {
                            $("#page-products-container").html(data);
                        })
                        .fail(function () {
                            alert("Spiacenti, si è verificato un errore nel caricamento dei prodotti interattivi della pagina");
                        })
                        .always(function () {
                            App.hide_loader();
                        });
                }
                else {
                    App.hide_loader();
                    App.edit_iflyer_wpag.load_products();
                }
            })
            .fail(function () {
                App.hide_loader();
                alert("save_info_interactivity error");
            })
            .always(function () {
            });
    },

    load_edit_specs_interactivity_modal: function () {
        App.show_loader();
        $.ajax({
            method: "GET",
            url: "/interactive-flyers/" + App.edit_interactive_flyer.flyer_id + "/products/" + App.edit_interactive_flyer.current_edit_interactive_product_id + "/interactivities/specs/edit"
        })
            .done(function (data) {
                $("#edit-specs-interactivity-modal-container").html(data);
                $("#specs-interactivity-modal").modal("show");
            })
            .fail(function () {
                alert("load_specs_recipe_interactivity_modal error");
            })
            .always(function () {
                App.hide_loader();
            });
    },

    save_specs_interactivity: function () {
        App.show_loader();

        var form_data = new FormData();

        if ($("#edit-specs-interactivity_image_file")[0].files) {
            var image_file_data = $("#edit-specs-interactivity_image_file")[0].files[0];
            form_data.append("image_file", image_file_data);
        }
        form_data.append("title", $("#edit-specs-interactivity_title").val());
        form_data.append("content_text", $("#edit-specs-interactivity_content-text").val());
        if ($("#edit-specs-interactivity_active").prop('checked')) {
            form_data.append("active", "true");
        }
        $.ajax({
            method: "POST",
            url: "/interactive-flyers/" + App.edit_interactive_flyer.flyer_id + "/products/" + App.edit_interactive_flyer.current_edit_interactive_product_id + "/interactivities/specs/update",
            contentType: false,
            processData: false,
            data: form_data
        })
            .done(function (data) {
                $("#specs-interactivity-modal").modal("hide");
                $("#specs-interactivity-badge-container").html(data.active ? App.edit_product_interactivity.interactivity_present_badge : App.edit_product_interactivity.interactivity_not_present_badge);

                if (App.edit_interactive_flyer.page_selected != null) {
                    $.ajax({
                        method: "GET",
                        url: "/interactive-flyer/" + App.edit_interactive_flyer.flyer_id + "/products",
                        data: {
                            page_number: App.edit_interactive_flyer.page_selected
                        }
                    })
                        .done(function (data) {
                            $("#page-products-container").html(data);
                        })
                        .fail(function () {
                            alert("Spiacenti, si è verificato un errore nel caricamento dei prodotti interattivi della pagina");
                        })
                        .always(function () {
                            App.hide_loader();
                        });
                }
                else {
                    App.hide_loader();
                    App.edit_iflyer_wpag.load_products();
                }
            })
            .fail(function () {
                App.hide_loader();
                alert("save_specs_interactivity error");
            })
            .always(function () {
            });
    },
}