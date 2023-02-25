/* jshint esversion: 6 */
const POLOTNO_API_URL = "https://ingraph-api.interattivo.net/api/"
let PolotnoIntegrationClass = class PolotnoIntegration {

    constructor(clientId, flyerId) {
        this.flyerId = flyerId;
        this.clientId = clientId;
        $('.polotno-create').on('click',(elmnt) => {
            let imageType = $(elmnt.target).attr('data-type');
            let imageFormat = ''
            let tabId = ''
            if($(elmnt.target).attr('data-format')){
                imageFormat = $(elmnt.target).attr('data-format');
            }
            if($(elmnt.target).attr('data-id')){
                tabId = $(elmnt.target).attr('data-id');
            }
            this.createPolotnoImage('new', imageType, imageFormat, tabId) ;
        });
        $('.polotno-choose-edit').click((elmnt) => {
            let imageType = $(elmnt.target).attr('data-type');
            let imageFormat = ''
            if($(elmnt.target).data('format')){
                imageFormat = $(elmnt.target).data('format');
            }
            this.openModalPolotnoTemplate(imageType,imageFormat);
        });
    }

    createPolotnoImage(action, imageType, imageFormat='0', tabId="") {
        this.getFormatTypesList(imageType, imageFormat, (formatId) => {
            let response = this.getPolotnoToken('new', formatId, null, imageType, null, tabId);
            response
                .done((data) => {
                    if (data.success) {
                        window.location = `https://ingraph.interattivo.net/?token=${data.token}`;
                    }
                })
                .fail((data) => {
                    console.log(data);
                    this.errorMessage();
                });
        });
    }

    getPolotnoToken(action, formatId, templateId, type, url=null,tabId=null) {
        const formData = new FormData();
        if (this.flyerId) {
            formData.append('interactive_flyer_id', this.flyerId);
        }
        formData.append('action', action);
        formData.append('type', type);
        if (formatId) {
            formData.append('id_format', formatId);
        }
        if (templateId) {
            formData.append('id_template', templateId);
        }
        if (url) {
            formData.append('template_url', url);
        }
        if (tabId) {
            formData.append('tab_id', tabId);
        }
        return $.ajax({
            method: "POST",
            url: '/it' + window.reverse('builder:polotno_auth_api'),
            data: formData,
            contentType: false,
            processData: false,
        }); 
    }

    getFormatTypesList(imageType, imageFormat, callback) {
        var format_array = {
            'Footer large':'1',
            'Header large':'2',
            'Header small':'3',
            'Indice template':'4',
            'Catalogo A4':'5',
            'Catalogo Template':'6',
            'clientIcon':'7',
            'ogImageMeta':'8',
            'ogImageMeta_mobile':'9',
            'category_banner':'10',
            'category_banner_mobile':'11',
            'product_banner':'12',
            'Volantino A4':'13',
            'Volantino quadrato':'14',
            'Indice A4':'15',
            'Indice quadrato':'16',
            'Grafica condivisione Facebook':'17',
            'clientIconC':'18',
            'brandImageC':'19',
            'logo_full':'26',
        };
        
        if (imageType  === '4') {
            $.ajax({
                method: "POST",
                url: POLOTNO_API_URL + "get-index-by-format/",
                data:{
                    'id_format':imageFormat,
                }
            })
                .done((data) => {
                    
                    callback(data.data[0].id);
                })
                .fail((data) => {
                    console.log(data);


                });
        } else {
            $.ajax({
                method: "GET",
                url: POLOTNO_API_URL + "get-format-list/",
            })
                .done((data) => {
                    if (data.success) {
                        data.data.forEach((item) => {
                            if (format_array[imageType] ==  item.id || imageType ==  item.name || imageType ==  item.id) {
                                callback(item.id);
                            }
                            // todo aggiungi altri formati
                        });
                    }
                })
                .fail((data) => {
                    console.log(data);
                    this.errorMessage();
                });
        }
    }

    openModalPolotnoTemplate(imageType,imageFormat) {
        this.getFormatTypesList(imageType,imageFormat, (formatId) => {
            this.getTemplateList(formatId, imageType);
        });
        $('#add-index-modal').modal('hide');
        $('#polotno-templates-modal').modal('show');
    }

    getTemplateList(formatId, imageType) {
        $.ajax({
            method: "POST",
            url: POLOTNO_API_URL + 'get-client-templates/',
            data: {
                id_client: this.clientId,
                id_format: formatId,
            },
        })
            .done((data) => {
                if (data.success) {
                    $('#container-templates-list').html('');
                    data.data.forEach((item) => {
                        const htmlIndexPage =
                            `<div class="index-div col-4 mb-2 d-inline-flex flex-column flex-end justify-content-end">
                                <img src="${item.url}" alt="" class="w-100 mb-1" style="width:200px;">
                                <div>
                                    <button class="polotno-choose-template index-div-button btn btn-volantino btn-yellow py-1 px-2 ml-1"
                                        data-url="${item.url}"
                                        data-type="${imageType}"
                                        data-id="${item.id}">
                                        ${gettext('Scegli')}
                                    </button>
                                    <button class="polotno-edit-template index-div-button btn btn-volantino btn-violet py-1 px-2"
                                        data-id="${item.id}"
                                        data-type="${imageType}">
                                        ${gettext('Modifica')}
                                    </button>
                                <div>

                            </div>`;
                        $('#container-templates-list').append(htmlIndexPage);
                    });

                    $('.polotno-edit-template').click((elmnt) => {
                        let imageType = $(elmnt.target).attr('data-type');
                        let templateId = $(elmnt.target).attr('data-id');
                        this.editPolotnoTemplate(templateId, imageType);
                    });
                    $('.polotno-choose-template').click((elmnt) => {
                        let url = $(elmnt.target).attr('data-url');
                        let imageType = $(elmnt.target).attr('data-type');
                        let templateId = $(elmnt.target).attr('data-id');
                        this.choosePolotnoTemplate(templateId, imageType, url);
                    });
                }
            })
            .fail((data) => {
                console.log('error',data);
                this.errorMessage();
            });
    }

    editPolotnoTemplate(templateId, imageType) {
        let response = this.getPolotnoToken('upd', null, templateId, imageType);
        response
            .done((data) => {
                if (data.success) {
                    window.location = `https://ingraph.interattivo.net/?token=${data.token}`;
                }
            })
            .fail(() => {
                this.errorMessage();
            });
    }

    choosePolotnoTemplate(templateId, imageType, url) {
        App.show_loader();
        let response = this.getPolotnoToken('choose', null, templateId, imageType, url);
        response
            .done((data) => {
                if (data.success) {
                    window.location = `${window.reverse('builder:polotno_api')}?token=${data.token}&client_id=${this.clientId}`;
                }
            })
            .fail(() => {
                this.errorMessage();
            })
            .always(() =>{
                App.hide_loader();
            });
    }

    errorMessage(message=null) {
        if (!message) {
            message = `${gettext('Qualcosa è andato storto!')}`;
        }
        Swal.fire({
            icon: 'error',
            title: `${gettext('Oops...')}`,
            text: message,
        });
    }
};