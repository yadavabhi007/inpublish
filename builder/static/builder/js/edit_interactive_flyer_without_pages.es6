App.edit_iflyer_wpag = {
    flyer_id: null,
    current_edit_interactive_product_id: null,
    project_items: [],
    selected_item_id: null,

    init: function (flyer_id) {
        App.show_loader();
        App.edit_iflyer_wpag.init_numeral();
        App.edit_iflyer_wpag.flyer_id = flyer_id;
        App.edit_interactive_flyer.flyer_id = flyer_id;
        App.edit_iflyer_wpag.load_project_items();
        App.edit_iflyer_wpag.load_products();
        App.edit_iflyer_wpag.init_category_select();
        App.edit_iflyer_wpag.init_varieties_token_input();
        App.edit_iflyer_wpag.init_price_computation_select();
    },

    init_numeral: function () {
        numeral.register('locale', 'it', {
            delimiters: {
                thousands: '',
                decimal: ','
            },
            abbreviations: {
                thousand: 'k',
                million: 'm',
                billion: 'b',
                trillion: 't'
            },
            ordinal: function (number) {
                return number === 1 ? 'er' : 'ème';
            },
            currency: {
                symbol: '€'
            }
        });
        numeral.locale("it");
    },

    load_products: function () {
        $.ajax({
            method: "GET",
            url: "/interactive-flyer/" + App.edit_iflyer_wpag.flyer_id + "/all-products"
        })
            .done(function (data) {
                // App.edit_interactive_flyer.page_products = data;
                // App.edit_interactive_flyer.init_products_table();
                $("#products-container").html(data);
                $("#flyer-products-table").DataTable();
                App.hide_loader();
            })
            .fail(function () {
                alert("Spiacenti, si è verificato un errore nel caricamento dei prodotti interattivi");
                App.hide_loader();
            })
            .always(function () {
            });
    },

    create_interactive_product: function () {
        App.show_loader();
        $("#create-product-card").hide();
        $("#new-product-card").show();
        App.hide_loader();
    },

    load_project_items: function () {
        $.ajax({
            method: "GET",
            url: "/interactive-flyer/" + App.edit_iflyer_wpag.flyer_id + "/project-items"
        })
            .done(function (data) {
                App.edit_iflyer_wpag.project_items = data;
                App.edit_iflyer_wpag.init_items_table();
            })
            .fail(function () {
                alert("load_project_items error");
            })
            .always(function () {
            });
    },

    init_items_table: function () {
        $('#items-table').DataTable({
            data: App.edit_iflyer_wpag.project_items,
            columns: [
                { data: 'field1' },
                { data: 'field2' },
                { data: 'field3' },
                { data: 'field4' },
                {
                    data: null,
                    render: function (data, type, row) {
                        return '<button class="btn btn-secondary btn-sm" onclick="App.edit_iflyer_wpag.select_item(' + row.id + ')">seleziona</button>';
                    }
                }
            ]
        });
    },

    select_item: function (item_id) {
        App.show_loader();

        $('#project-items-modal').modal('hide');
        App.edit_iflyer_wpag.selected_item_id = item_id;
        $("#item_id").val(App.edit_iflyer_wpag.selected_item_id);
        let item = App.edit_iflyer_wpag.project_items.find(x => x.id == App.edit_iflyer_wpag.selected_item_id)

        $.ajax({
            method: "GET",
            url: "/load-item-info/" + App.edit_iflyer_wpag.flyer_id + "/",
            data: {
                item_id: App.edit_iflyer_wpag.selected_item_id
            }
        })
            .done(function (data) {
                $("#new-interactive-product-form_product_uid").val(data.product_id);
                $("#new-interactive-product-form_field1").val(data.field1);
                $("#new-interactive-product-form_field2").val(data.field2);
                $("#new-interactive-product-form_field3").val(data.field3);
                $("#new-interactive-product-form_field4").val(data.field4);
                $("#new-interactive-product-form_grammage").val(data.grammage);
                $("#new-interactive-product-form_price_with_iva").val(data.price_with_iva);
                $("#new-interactive-product-form_price_for_kg").val(data.price_for_kg);
                $("#new-interactive-product-form_available_pieces").val(data.available_pieces);
                $("#new-interactive-product-form_max_purchasable_pieces").val(data.max_purchasable_pieces);
                $("#new-interactive-product-form_points").val(data.points);
                $("#new-interactive-product-form_fidelity_product").prop('checked', data.fidelity_product);
                $("#new-interactive-product-form_focus").prop('checked', data.focus);
                $("#new-interactive-product-form_pam").prop('checked', data.pam);
                $("#new-interactive-product-form_three_for_two").prop('checked', data.three_for_two);
                $("#new-interactive-product-form_one_and_one_gratis").prop('checked', data.one_and_one_gratis);
                $("#new-interactive-product-form_underpriced_product").prop('checked', data.underpriced_product);
                $("#new-interactive-product-form_category").val(data.category);
                if (data.category != "") {
                    App.edit_iflyer_wpag.get_subcategories_select_by_category(data.category).then(function (response) {
                        $("#new-interactive-product-form_subcategory").empty();
                        $("#new-interactive-product-form_subcategory").html('<option value=""></option>');
                        response.forEach(item => $("#new-interactive-product-form_subcategory").append('<option value="' + item + '">' + item + '</option>'));
                        $("#new-interactive-product-form_subcategory").prop('disabled', false);

                        $("#new-interactive-product-form_subcategory").val(data.subcategory);
                    }).catch(function (message) {
                        console.log(message);
                    });
                }
                $("#new-interactive-product-form_save_categories_on_catalog").prop("checked", true);
                $("#save_categories_on_catalog_wrapper").show();
                App.edit_iflyer_wpag.update_price_computation();
            })
            .fail(function () {
                alert("select_item error");
            })
            .always(function () {
                App.hide_loader();
            });
    },

    get_subcategories_select_by_category: function (category) {
        return new Promise(function (resolve, reject) {
            $.ajax({
                method: "GET",
                url: "/subcategories-by-category",
                data: {
                    category: category,
                }
            })
                .done(function (data) {
                    resolve(data);
                })
                .fail(function () {
                    reject("Spiacenti, si è verificato un errore imprevisto durante il recupero delle sottocategorie");
                });
        });
    },

    update_price_computation: function () {
        var type = $("#new-interactive-product-form_price_computation_type").val();
        if (type == "pz") {
            var price_label = "€ " + numeral(parseFloat($("#new-interactive-product-form_price_with_iva").val())).format("0.00");
            $("#new-interactive-product-form_price_label").val(price_label);
            var grocery_label = "pz.";
            $("#new-interactive-product-form_grocery_label").val(grocery_label);
            var equivalence = 1;
            $("#new-interactive-product-form_equivalence").val(equivalence);
            var quantity_step = 1;
            $("#new-interactive-product-form_quantity_step").val(quantity_step);
        }
        if (type == "kg-kg") {
            var price_label = "€ " + numeral(parseFloat($("#new-interactive-product-form_price_with_iva").val())).format("0.00") + " al Kg";
            $("#new-interactive-product-form_price_label").val(price_label);
            var grocery_label = "kg.";
            $("#new-interactive-product-form_grocery_label").val(grocery_label);
            var equivalence = 1;
            $("#new-interactive-product-form_equivalence").val(equivalence);
            var quantity_step = 1;
            $("#new-interactive-product-form_quantity_step").val(quantity_step);
        }
        if (type == "kg-etto") {
            var price_label = "€ " + numeral(parseFloat($("#new-interactive-product-form_price_with_iva").val())).format("0.00") + " al Kg";
            $("#new-interactive-product-form_price_label").val(price_label);
            var grocery_label = "etto/i";
            $("#new-interactive-product-form_grocery_label").val(grocery_label);
            var equivalence = 10;
            $("#new-interactive-product-form_equivalence").val(equivalence);
            var quantity_step = 1;
            $("#new-interactive-product-form_quantity_step").val(quantity_step);
        }
        if (type == "kg-gr") {
            var price_label = "€ " + numeral(parseFloat($("#new-interactive-product-form_price_with_iva").val())).format("0.00") + " al Kg";
            $("#new-interactive-product-form_price_label").val(price_label);
            var grocery_label = "gr.";
            $("#new-interactive-product-form_grocery_label").val(grocery_label);
            var equivalence = 10;
            $("#new-interactive-product-form_equivalence").val(equivalence);
            var quantity_step = 100;
            $("#new-interactive-product-form_quantity_step").val(quantity_step);
        }
        if (type == "etto-etto") {
            var price_label = "€ " + numeral(parseFloat($("#new-interactive-product-form_price_with_iva").val())).format("0.00") + " l'etto";
            $("#new-interactive-product-form_price_label").val(price_label);
            var grocery_label = "etto/i";
            $("#new-interactive-product-form_grocery_label").val(grocery_label);
            var equivalence = 1;
            $("#new-interactive-product-form_equivalence").val(equivalence);
            var quantity_step = 1;
            $("#new-interactive-product-form_quantity_step").val(quantity_step);
        }
    },

    init_category_select: function () {
        $("#new-interactive-product-form_category").change(function () {
            let category = $(this).val();
            App.edit_iflyer_wpag.get_subcategories_select_by_category(category).then(function (response) {
                $("#new-interactive-product-form_subcategory").empty();
                $("#new-interactive-product-form_subcategory").html('<option value=""></option>');
                response.forEach(item => $("#new-interactive-product-form_subcategory").append('<option value="' + item + '">' + item + '</option>'));
                $("#new-interactive-product-form_subcategory").prop('disabled', false);
            });
        });
    },

    init_varieties_token_input: function () {
        $("#new-interactive-product-form_varieties").tagsinput();
    },

    init_price_computation_select: function () {
        $("#new-interactive-product-form_price_computation_type").change(function () {
            App.edit_iflyer_wpag.update_price_computation();
        });
    },

    cancel_interactive_product_creation: function () {
        App.edit_iflyer_wpag.reset_product_creation();
    },

    reset_product_creation: function () {
        $("#create-product-card").show();
        $("#new-product-card").hide();
        $("#item_id").val("");
        App.edit_iflyer_wpag.selected_item_id = null;
        $("#item_description").val("");

        $("#new-interactive-product-form_product_uid").val("");
        $("#new-interactive-product-form_field1").val("");
        $("#new-interactive-product-form_field2").val("");
        $("#new-interactive-product-form_field3").val("");
        $("#new-interactive-product-form_field4").val("");
        $("#new-interactive-product-form_grammage").val("");
        $("#new-interactive-product-form_price_with_iva").val("");
        $("#new-interactive-product-form_price_for_kg").val("");
        $("#new-interactive-product-form_available_pieces").val("");
        $("#new-interactive-product-form_max_purchasable_pieces").val("");
        $("#new-interactive-product-form_points").val("");
        $("#new-interactive-product-form_fidelity_product").prop('checked', false);
        $("#new-interactive-product-form_focus").prop('checked', false);
        $("#new-interactive-product-form_pam").prop('checked', false);
        $("#new-interactive-product-form_three_for_two").prop('checked', false);
        $("#new-interactive-product-form_one_and_one_gratis").prop('checked', false);
        $("#new-interactive-product-form_underpriced_product").prop('checked', false);
        $("#new-interactive-product-form_category").val("");
        $("#new-interactive-product-form_subcategory").empty();
        $("#new-interactive-product-form_save_categories_on_catalog").prop("checked", false);
        $("#save_categories_on_catalog_wrapper").hide();
        $("#new-interactive-product-form_varieties").tagsinput('removeAll');
        $("#new-interactive-product-form_equivalence").val("");
        $("#new-interactive-product-form_quantity_step").val("");
        $("#new-interactive-product-form_price_label").val("");
        $("#new-interactive-product-form_grocery_label").val("");
    },

    save_interactive_product: function () {
        App.show_loader();

        const formData = new FormData();

        // formData.append('cropped_image', blob, "cropped_image.png");
        formData.append('item_id', App.edit_iflyer_wpag.selected_item_id);
        formData.append('product_uid', $("#new-interactive-product-form_product_uid").val());
        // formData.append('blueprint_top', $("#blueprint_top").val());
        // formData.append('blueprint_left', $("#blueprint_left").val());
        // formData.append('blueprint_width', $("#blueprint_width").val());
        // formData.append('blueprint_height', $("#blueprint_height").val());
        // formData.append('page', App.edit_interactive_flyer.page_selected);
        formData.append('field1', $("#new-interactive-product-form_field1").val());
        formData.append('field2', $("#new-interactive-product-form_field2").val());
        formData.append('field3', $("#new-interactive-product-form_field3").val());
        formData.append('field4', $("#new-interactive-product-form_field4").val());
        formData.append('grammage', $("#new-interactive-product-form_grammage").val());
        formData.append('price_with_iva', $("#new-interactive-product-form_price_with_iva").val());
        formData.append('price_for_kg', $("#new-interactive-product-form_price_for_kg").val());
        formData.append('available_pieces', $("#new-interactive-product-form_available_pieces").val());
        formData.append('max_purchasable_pieces', $("#new-interactive-product-form_max_purchasable_pieces").val());
        formData.append('points', $("#new-interactive-product-form_points").val());
        if ($("#new-interactive-product-form_fidelity_product").prop('checked')) {
            formData.append('fidelity_product', "true");
        }
        if ($("#new-interactive-product-form_focus").prop('checked')) {
            formData.append('focus', "true");
        }
        if ($("#new-interactive-product-form_pam").prop('checked')) {
            formData.append('pam', "true");
        }
        if ($("#new-interactive-product-form_three_for_two").prop('checked')) {
            formData.append('three_for_two', "true");
        }
        if ($("#new-interactive-product-form_one_and_one_gratis").prop('checked')) {
            formData.append('one_and_one_gratis', "true");
        }
        if ($("#new-interactive-product-form_underpriced_product").prop('checked')) {
            formData.append('underpriced_product', "true");
        }
        formData.append('category', $("#new-interactive-product-form_category").val());
        formData.append('subcategory', ($("#new-interactive-product-form_subcategory").val() == null ? "" :  $("#new-interactive-product-form_subcategory").val()));
        if ($("#new-interactive-product-form_save_categories_on_catalog").prop('checked')) {
            formData.append('save_categories_on_catalog', "true");
        }

        formData.append('varieties', $("#new-interactive-product-form_varieties").val());
        formData.append('equivalence', $("#new-interactive-product-form_equivalence").val());
        formData.append('quantity_step', $("#new-interactive-product-form_quantity_step").val());
        formData.append('price_label', $("#new-interactive-product-form_price_label").val());
        formData.append('grocery_label', $("#new-interactive-product-form_grocery_label").val());

        $.ajax({
            method: "POST",
            url: "/interactive-flyer/" + App.edit_iflyer_wpag.flyer_id + "/create-product",
            data: formData,
            processData: false,
            contentType: false,
        })
            .done(function (data) {
                if (data.status == "created") {
                    App.edit_iflyer_wpag.reset_product_creation();
                    App.edit_iflyer_wpag.load_products();
                    $('#product-created-modal').modal('show');
                }
            })
            .fail(function () {
                alert("save_interactive_product error");
            })
            .always(function () {
                App.hide_loader();
            });
    },

    delete_interactive_product: function (product_id) {
        if (confirm("Sei sicuro di voler cancellare il prodotto interattivo?")) {
            App.show_loader();
            $.ajax({
                method: "POST",
                url: "/interactive-flyer-product/" + product_id + "/delete"
            })
                .done(function (data) {
                    if (data.status == "deleted") {
                        $('#product-deleted-modal').modal('show');
                        App.edit_iflyer_wpag.load_products();
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

    edit_interactive_product: function (interactive_product_id) {
        App.edit_iflyer_wpag.current_edit_interactive_product_id = interactive_product_id;
        App.edit_interactive_flyer.current_edit_interactive_product_id = interactive_product_id;
        App.show_loader();
        $.ajax({
            method: "GET",
            url: "/interactive-flyers/" + App.edit_iflyer_wpag.flyer_id + "/interactive-products/" + App.edit_iflyer_wpag.current_edit_interactive_product_id + "/edit"
        })
            .done(function (data) {
                $("#edit-product-container").html(data);
                $("#create-product-card").hide();
                $('#right').animate({
                    scrollTop: 0
                }, 'slow');
                App.hide_loader();
            })
            .fail(function () {
                alert("Spiacenti, si è verificato un errore nel caricamento del prodotto interattivo");
            });
    },

    cancel_interactive_product_edit: function () {
        App.edit_iflyer_wpag.reset_product_edit();
    },

    reset_product_edit: function () {
        $("#edit-product-container").empty();
        $("#create-product-card").show();
        App.edit_iflyer_wpag.current_edit_interactive_product_id = null;
    },

    init_edit_product_category_select: function () {
        $("#edit-interactive-product-form_category").change(function () {
            let category = $(this).val();
            App.edit_iflyer_wpag.get_subcategories_select_by_category(category).then(function (response) {
                $("#edit-interactive-product-form_subcategory").empty();
                $("#edit-interactive-product-form_subcategory").html('<option value=""></option>');
                response.forEach(item => $("#edit-interactive-product-form_subcategory").append('<option value="' + item + '">' + item + '</option>'));
                $("#edit-interactive-product-form_subcategory").prop('disabled', false);
            });
        });
    },

    update_price_computation_edit: function () {
        var type = $("#edit-interactive-product-form_price_computation_type").val();
        if (type == "pz") {
            var price_label = "€ " + numeral(parseFloat($("#edit-interactive-product-form_price_with_iva").val())).format("0.00");
            $("#edit-interactive-product-form_price_label").val(price_label);
            var grocery_label = "pz.";
            $("#edit-interactive-product-form_grocery_label").val(grocery_label);
            var equivalence = 1;
            $("#edit-interactive-product-form_equivalence").val(equivalence);
            var quantity_step = 1;
            $("#edit-interactive-product-form_quantity_step").val(quantity_step);
        }
        if (type == "kg-kg") {
            var price_label = "€ " + numeral(parseFloat($("#edit-interactive-product-form_price_with_iva").val())).format("0.00") + " al Kg";
            $("#edit-interactive-product-form_price_label").val(price_label);
            var grocery_label = "kg.";
            $("#edit-interactive-product-form_grocery_label").val(grocery_label);
            var equivalence = 1;
            $("#edit-interactive-product-form_equivalence").val(equivalence);
            var quantity_step = 1;
            $("#edit-interactive-product-form_quantity_step").val(quantity_step);
        }
        if (type == "kg-etto") {
            var price_label = "€ " + numeral(parseFloat($("#edit-interactive-product-form_price_with_iva").val())).format("0.00") + " al Kg";
            $("#edit-interactive-product-form_price_label").val(price_label);
            var grocery_label = "etto/i";
            $("#edit-interactive-product-form_grocery_label").val(grocery_label);
            var equivalence = 10;
            $("#edit-interactive-product-form_equivalence").val(equivalence);
            var quantity_step = 1;
            $("#edit-interactive-product-form_quantity_step").val(quantity_step);
        }
        if (type == "kg-gr") {
            var price_label = "€ " + numeral(parseFloat($("#edit-interactive-product-form_price_with_iva").val())).format("0.00") + " al Kg";
            $("#edit-interactive-product-form_price_label").val(price_label);
            var grocery_label = "gr.";
            $("#edit-interactive-product-form_grocery_label").val(grocery_label);
            var equivalence = 1000;
            $("#edit-interactive-product-form_equivalence").val(equivalence);
            var quantity_step = 100;
            $("#edit-interactive-product-form_quantity_step").val(quantity_step);
        }
        if (type == "etto-etto") {
            var price_label = "€ " + numeral(parseFloat($("#edit-interactive-product-form_price_with_iva").val())).format("0.00") + " l'etto";
            $("#edit-interactive-product-form_price_label").val(price_label);
            var grocery_label = "etto/i";
            $("#edit-interactive-product-form_grocery_label").val(grocery_label);
            var equivalence = 1;
            $("#edit-interactive-product-form_equivalence").val(equivalence);
            var quantity_step = 1;
            $("#edit-interactive-product-form_quantity_step").val(quantity_step);
        }
    },

    update_interactive_product: function () {
        App.show_loader();

        const formData = new FormData();

        // formData.append('cropped_image', blob, "cropped_image.png");
        // formData.append('blueprint_top', $("#blueprint_top_edit").val());
        // formData.append('blueprint_left', $("#blueprint_left_edit").val());
        // formData.append('blueprint_width', $("#blueprint_width_edit").val());
        // formData.append('blueprint_height', $("#blueprint_height_edit").val());
        formData.append('product_uid', $("#edit-interactive-product-form_product_uid").val());
        formData.append('field1', $("#edit-interactive-product-form_field1").val());
        formData.append('field2', $("#edit-interactive-product-form_field2").val());
        formData.append('field3', $("#edit-interactive-product-form_field3").val());
        formData.append('field4', $("#edit-interactive-product-form_field4").val());

        formData.append('category', $("#edit-interactive-product-form_category").val());
        formData.append('subcategory', $("#edit-interactive-product-form_subcategory").val());
        if ($("#edit-interactive-product-form_save_categories_on_catalog").prop('checked')) {
            formData.append('save_categories_on_catalog', "true");
        }

        formData.append('grammage', $("#edit-interactive-product-form_grammage").val());
        formData.append('price_with_iva', $("#edit-interactive-product-form_price_with_iva").val());
        formData.append('price_for_kg', $("#edit-interactive-product-form_price_for_kg").val());
        formData.append('available_pieces', $("#edit-interactive-product-form_available_pieces").val());
        formData.append('max_purchasable_pieces', $("#edit-interactive-product-form_max_purchasable_pieces").val());
        formData.append('points', $("#edit-interactive-product-form_points").val());
        if ($("#edit-interactive-product-form_fidelity_product").prop('checked')) {
            formData.append('fidelity_product', "true");
        }
        if ($("#edit-interactive-product-form_focus").prop('checked')) {
            formData.append('focus', "true");
        }
        if ($("#edit-interactive-product-form_pam").prop('checked')) {
            formData.append('pam', "true");
        }
        if ($("#edit-interactive-product-form_three_for_two").prop('checked')) {
            formData.append('three_for_two', "true");
        }
        if ($("#edit-interactive-product-form_one_and_one_gratis").prop('checked')) {
            formData.append('one_and_one_gratis', "true");
        }
        if ($("#edit-interactive-product-form_underpriced_product").prop('checked')) {
            formData.append('underpriced_product', "true");
        }

        formData.append('varieties', $("#edit-interactive-product-form_varieties").val());
        formData.append('equivalence', $("#edit-interactive-product-form_equivalence").val());
        formData.append('quantity_step', $("#edit-interactive-product-form_quantity_step").val());
        formData.append('price_label', $("#edit-interactive-product-form_price_label").val());
        formData.append('grocery_label', $("#edit-interactive-product-form_grocery_label").val());

        $.ajax({
            method: "POST",
            url: "/interactive-flyers/" + App.edit_iflyer_wpag.flyer_id + "/interactive-products/" + App.edit_iflyer_wpag.current_edit_interactive_product_id + "/update",
            data: formData,
            processData: false,
            contentType: false,
        })
            .done(function (data) {
                if (data.status == "updated") {
                    App.edit_iflyer_wpag.reset_product_edit();
                    App.edit_iflyer_wpag.load_products();
                    $('#product-updated-modal').modal('show');
                }
            })
            .fail(function () {
                alert("Spiacenti, si è verificato un errore durante l'aggiornamento del prodotto interattivo");
            })
            .always(function () {
                App.hide_loader();
            });
    },

    load_product_images_modal: function () {
        App.show_loader();
        $.ajax({
            method: "GET",
            url: "/interactive-flyers/" + App.edit_iflyer_wpag.flyer_id + "/products/" + App.edit_iflyer_wpag.current_edit_interactive_product_id + "/images"
        })
            .done(function (data) {
                $("#product-images-modal-container").html(data);
                $("#product-images-modal").modal("show");
            })
            .fail(function () {
                alert("load_product_images_modal error");
            })
            .always(function () {
                App.hide_loader();
            });
    },
}