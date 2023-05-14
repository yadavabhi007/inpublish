/* jshint esversion: 6 */

let GiodicartManagerClass = class GiodicartManager {

    constructor(flyer_id) {
        this.reactor = reactorSingleton.getInstance();
        this.cropper_item = null;
        this.flyer_id = flyer_id;
        this.page_selected = 1;
        this.reactor.addEventListener('go_to_page', (page_selected) => {
            this.page_selected = page_selected;
        });
        this.reactor.addEventListener('save_product', (modify) => {
            this.saveProduct(modify);
        });
        this.reactor.addEventListener('cropped_image', (cropper_item) => {
            this.cropper_item = cropper_item;
        });
        $("#search-skul").keypress((event) => {
            var keycode = (event.keyCode ? event.keyCode : event.which);
            if(keycode == '13'){
                this.searchProductBySkul();
            }
        });

        // disabilito i campi di giodicart
        $('.giodicart input').attr('disabled', 'true');
        $('.giodicart select').attr('disabled', 'true');
        $('.giodicart textarea').attr('disabled', 'true');
    }

    openSearchProductModal() {
        $('#giodicart-search-result-table').addClass("d-none");
        $('#giodicart-search-products-modal').modal('show');
    }

    searchProductBySkul() {
        App.show_loader("#giodicart-search-products-modal div.modal-body");
        const formData = new FormData();
        formData.append('skul', $("#search-skul").val());
        $.ajax({
            method: "POST",
            url: '/it' + window.reverse('builder:search_giodicart_product_api'),
            data: formData,
            contentType: false,
            processData: false,
        })
            .done((data) => {
                const dataArray = [data, ];
                const itemsTable = $('#giodicart-search-result-table');
                itemsTable.DataTable().destroy();
                const cleaned_code = dataArray[0].codice_interno_insegna.replaceAll('.','')
                if(data.success){
                    itemsTable.DataTable({
                        searching: false,
                        info: false,
                        lengthChange: false,
                        language: {
                            url: '/static/gull-admin/js/plugins/localization/italian.json'
                        },
                        data:dataArray ,
                        columns: [
                            {
                                data: null,
                                render: function (data, type, row) {
                                    return `${row.product_id}`;
                                }
                            },
                            {data: 'field1'},
                            {data: 'field2'},
                            {data: 'field3'},
                            {data: 'field4'},
                            {
                                data: null,
                                render: function (data, type, row) {
                                    return `<div id="giodicart-${cleaned_code}" class="d-none">${JSON.stringify(row)}</div><button class="btn btn-secondary btn-sm" attr-product-id="${row.codice_interno_insegna}"
                                                onclick="giodicartManager.productSelectedFromArchive(this);"
                                                >${gettext('Seleziona')}</button>`;
                                }
                            }
                        ]
                    });
                }else{
                    itemsTable.DataTable({
                        searching: false,
                        info: false,
                        lengthChange: false,
                        language: {
                            url: '/static/gull-admin/js/plugins/localization/italian.json'
                        },
                        data:data,
                        columns:[
                            {data:'info'},
                            {data:''},
                            {data:''},
                            {data:''},
                            {data:''},
                            {data:''},
                        ]
                    });
                }
                itemsTable.removeClass("d-none");
            })
            .fail((data) => {
                this.reactor.dispatchEvent('error_message', data.info);
            }).always(() => {
                App.hide_loader("#giodicart-search-products-modal div.modal-body");
            });
    }

    productSelectedFromArchive(obj) {
        App.show_loader("#giodicart-search-products-modal div.modal-body");
        $("#search-skul").val("");
        const codiceProdotto = $(obj).attr('attr-product-id');

        const cleaned_code = codiceProdotto.replaceAll('.','')
        let data = JSON.parse($(`#giodicart-${cleaned_code}`).html());
        $('#json-giodicart-hidden').html(JSON.stringify(data));
        $('#json-giodicart').html(JSON.stringify(data)).beautifyJSON({
            type:"flexible",
            // highlight JSON on mouse hover
            hoverable:true,
            // make nested nodes collapsible
            collapsible:true,
            // enable colors
            color:true
        });
        let productId = `${data.product_id}`;
        if (data.product_id === "") {
            productId = data.codice_interno_insegna;
        }
        $('#i-product_codice_interno_insegna').val(productId);
        $('#i-product_field1').val(data.field1);
        $('#i-product_field2').val(data.field2);
        $('#i-product_field3').val(data.field3);
        $('#i-product_field4').val(data.field4);
        $('#i-product_descrizione_estesa').val(data.descrizione_estesa);
        $('#i-photo').val(data.photo);
        $('#strike-price').val(data.strike_price);
        $('#tdc').val(data.tdc);
        $('#stock').val(data.stock);
        $('#from').val(data.from);
        $('#discount-rate').val(data.discount_rate);
        if (data.promo) {
            $('#promo').attr('checked', true);
        }
        var price_field = '';
        for (let i = 0; i < data.prices.length; i++) {
            const price = data.prices[i];
            price_field = price_field + price.price + ' ';
        }
        $('#i-prices').val(price_field);
        $('#i-product_varieties').tagging('add',data.varieties);

        App.hide_loader("#giodicart-search-products-modal div.modal-body");
        $('#giodicart-search-products-modal').modal('hide');
    }

    saveProduct(modify) {
        App.show_loader();
        const formDataGiodicart = new FormData();

        let urlToSubmit = '/it' + window.reverse('builder:create_giodicart_product', this.flyer_id);
        const product_id = $("#i-product_id").val();
        if (product_id) {
            formDataGiodicart.append('id', product_id);
            urlToSubmit = '/it' + window.reverse('builder:update_giodicart_product', [this.flyer_id, product_id]);
        }

        formDataGiodicart.append('field1', $("#i-product_field1").val());
        formDataGiodicart.append('field2', $("#i-product_field2").val());
        formDataGiodicart.append('field3', $("#i-product_field3").val());
        formDataGiodicart.append('field4', $("#i-product_field4").val());
        formDataGiodicart.append('descrizione_estesa', $("#i-product_descrizione_estesa").val());
        formDataGiodicart.append('json', $('#json-giodicart-hidden').html());

        const tags = $("#i-product_varieties").tagging("getTags");
        formDataGiodicart.append('varieties', tags.join());

        formDataGiodicart.append('page', this.page_selected);
        formDataGiodicart.append('modify', modify);

        // for(var pair of formDataGiodicart.entries()) {
        //    console.log(pair[0]+ ', '+ pair[1]);
        // }

        try {
            this.cropper_item.cropper("getCroppedCanvas").toBlob((blob) => {
                formDataGiodicart.append('cropped_image', blob, "cropped_image.png");
                formDataGiodicart.append('blueprint_top', $("#i-product_blueprint_top").val());
                formDataGiodicart.append('blueprint_left', $("#i-product_blueprint_left").val());
                formDataGiodicart.append('blueprint_width', $("#i-product_blueprint_width").val());
                formDataGiodicart.append('blueprint_height', $("#i-product_blueprint_height").val());

                this.ajaxProduct(urlToSubmit, formDataGiodicart);
            });
        } catch (e) {
            this.ajaxProduct(urlToSubmit, formDataGiodicart);
        }
    }

    ajaxProduct(urlToSubmit, formDataGiodicart) {
        $.ajax({
            method: "POST",
            url: urlToSubmit,
            data: formDataGiodicart,
            contentType: false,
            processData: false,
        })
            .done((data) => {
                this.reactor.dispatchEvent('post_save_product', data);
            })
            .fail(() => {
                this.reactor.dispatchEvent('error_message');
            })
            .always(() => {
                App.hide_loader();
                this.reactor.dispatchEvent('release_interactivity_product');
            });
    }
};