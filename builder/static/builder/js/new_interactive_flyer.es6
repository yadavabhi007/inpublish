App.new_interactive_flyer = {

    selected_seller_id: null,

    init: function () {
        App.new_interactive_flyer.init_seller_select();
        App.new_interactive_flyer.init_form();
        App.new_interactive_flyer.init_affiliate_select();
        App.new_interactive_flyer.init_project_select();
    },

    init_form: function(){
        $("#create-interactive-flyer-form").submit(function(){
            if (! $("#name").val().trim()){
                return false;
            }
            // if (document.getElementById("flyer_pdf").files.length < 1){
            //     alert("Carica un PDF del volantino!");
            //     return false;
            // }
            // if (document.getElementById("flyer_pdf").files[0].type != "application/pdf"){
            //     alert("Il file deve essere un PDF!");
            //     return false;
            // }
            App.show_loader();
            return true;
        });
    },

    init_seller_select: function () {
        // $('#seller-select').select2({
        //     theme: "bootstrap4",
        //     placeholder: 'Seleziona un cliente'
        // });

        $('#seller-select').change(function () {
            App.show_loader($("#affiliate-container"));
            App.show_loader($("#project-container"));
            App.new_interactive_flyer.selected_seller_id = $(this).val();
            App.new_interactive_flyer.load_seller_affiliates_select();
            App.new_interactive_flyer.load_seller_projects_select();
        });

        try {
            var seller_id = JSON.parse(document.getElementById('seller_id').textContent);
            App.show_loader($("#affiliate-container"));
            App.show_loader($("#project-container"));
            App.new_interactive_flyer.selected_seller_id = seller_id;
            App.new_interactive_flyer.load_seller_affiliates_select();
            App.new_interactive_flyer.load_seller_projects_select();
        } catch (e) {}
    },

    init_affiliate_select: function () {
        // $('#affiliate-select').select2({
        //     theme: "bootstrap4",
        //     placeholder: 'Seleziona un affiliato'
        // });
    },

    init_project_select: function () {
    //     $('#project-select').select2({
    //         theme: "bootstrap4",
    //         placeholder: 'Seleziona progetti',
    //         multiple: true,
    //     });
    },

    load_seller_affiliates_select: function () {
        $.ajax({
            method: "GET",
            url: "/seller-affiliates-select",
            data: {
                seller_id: App.new_interactive_flyer.selected_seller_id
            }
        })
            .done(function (data) {
                let affSelect = $('#affiliate-select');
                affSelect.html("");
                data.affiliates.forEach((affiliate) => {
                    var opt = $("<option>").val(affiliate.id).text(affiliate.name);
                    affSelect.append(opt);
                });
                affSelect.trigger('change');
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
                seller_id: App.new_interactive_flyer.selected_seller_id
            }
        })
            .done(function (data) {
                let projSelect = $('#project-select');
                projSelect.html("");
                data.projects.forEach((project) => {
                    var opt = $("<option>").val(project.id).text(`${project.nome} (id: ${project.id})`);
                    projSelect.append(opt);
                });
                projSelect.trigger('change');
            })
            .fail(function () {
                alert("error");
            })
            .always(function () {
                App.hide_loader($("#project-container"));
            });
    }

}