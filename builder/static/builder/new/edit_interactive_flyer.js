/* jshint esversion: 6 */

let EditInteractiveFlyerClass = class EditInteractiveFlyer {

    constructor(flyer_id, flyer_pages, zip_generation_in_progress, clientId) {
        this.blueprint = {
            'top':25,
            'left':35,
            'height':35,
            'width':35
        };

        this.reactor = reactorSingleton.getInstance();
        this.reactor.registerEvent('go_to_page');
        this.reactor.registerEvent('save_product');
        this.reactor.registerEvent('post_save_product');
        this.reactor.registerEvent('change_page');
        this.reactor.registerEvent('error_message');
        this.reactor.registerEvent('cropped_image');
        this.reactor.addEventListener('save_product', (modify) => {
            if (JSON.parse($("#connector_type").html()) !== "giodicart") {
                this.saveProduct(modify);
            }
        });
        this.reactor.addEventListener('post_save_product', (data) => {
            if (data.status === "created") {
                this.productInPages[this.page_selected - 1].splice(0, 0, data.product);
                try {
                    this.blueprint.top = data.product.blueprint.top;
                    this.blueprint.left = data.product.blueprint.left;
                    this.blueprint.height = data.product.blueprint.height;
                    this.blueprint.width = data.product.blueprint.width;
                } catch (e) {}
            }
            if (data.status === "updated") {
                const index = this.searchProductIndex(data.product.id, 'id');
                this.productInPages[this.page_selected -1].splice(index, 1);
                this.productInPages[this.page_selected -1].splice(index, 0, data.product);
            }
            if (data.modify) {
                this.editProductFromPage(data.product);
                // this.undoInteractivity();
                this.changePage();
                setTimeout(function(){
                    $('#page-products-card').hide()
                },500)
                
            } else if(data.status === "error") {
                this.errorMessage(`${gettext(data.message)}`);
            } else {
                this.undoInteractivity();
                this.changePage();
            }
        });
        this.reactor.addEventListener('change_page', () => {
            this.changePage();
        });
        this.reactor.addEventListener('error_message', (message = null) => {
            this.errorMessage(message);
        });
        
        this.flyer_id = flyer_id;
        this.clientId = clientId;
        this.polotnoIntegration = new PolotnoIntegrationClass(clientId, flyer_id);
        this.permissionManager = new PermissionsManagerClass();
        this.page_selected = 1;
        this.flyer_pages = flyer_pages;
        this.pages = JSON.parse($('#pages').text());
        this.productInPages = {};
        this.pages_bar = $('#pages-bar');
        this.cards = [
            '#add-product-card', '#add-video-card', '#page-products-card', '#index-card',
            '#add-internal-link-index-card', '#add-external-link-index-card',
            '#add-external-link-card', '#add-internal-link-card', '#video-interactivities-card',
            '#external-link-interactivities-card', '#internal-link-interactivities-card',
        ];
        let taggingjs = $(".tagBox");
        taggingjs.tagging({
            "no-spacebar": true,
            "no-duplicate-callback": console.log,
        });
        taggingjs.on( "remove:after", ( el, text, tagging ) => {
          taggingjs.tagging( "valInput", "" );
        });
        this.boxes = $('#draw');
        const pageImg = $('#flyer-page-dimension');
        this.flyerDimensions = {
            'width': pageImg.attr('data-width'),
            'height': pageImg.attr('data-height')
        };
        this.cropper_item = null;
        this.last_cropper = null;

        if (zip_generation_in_progress) {
            App.show_loader("#content");
            this.setGeneratingPolling();
        }

        this.initPageBar();
        this.changePage();  // per disegnare i box dei prodotti al primo avvio
        this.initCategorySelect();
        this.getPriceLabels();
        // fix comma numbers
        const fields = ['#i-product_offer_price'];
        fields.forEach((fieldId) => {
            $(document).find(fieldId).keyup(function(evt){
                $(this).val($(this).val().replaceAll(',', '.'));
            });
        });
    }

    // region utils
    showHideMenuItems(typePage) {
        switch (typePage) {
            case 'index':
                $('#interactivity-product').addClass('d-none');
                $('#interactivity-video').addClass('d-none');

                $('#interactivity-product-external-link').addClass('d-none');
                $('#interactivity-product-internal-link').addClass('d-none');
                $('#interactivity-index-external-link').removeClass('d-none');
                $('#interactivity-index-internal-link').removeClass('d-none');
                break;

            case 'page':
                $('#interactivity-product').removeClass('d-none');
                $('#interactivity-video').removeClass('d-none');
                $('#interactivity-index-external-link').addClass('d-none');
                $('#interactivity-index-internal-link').addClass('d-none');
                $('#interactivity-product-external-link').removeClass('d-none');
                $('#interactivity-product-internal-link').removeClass('d-none');
                break;
        }
    }

    setElementIfEmpty(element, value, force = false) {
        if (force || element.val() === '') {
            element.val(value);
        }
    }

    populatePageNumberSelect(selectId) {
        const selectPageNumber = $(selectId);
        selectPageNumber.html('');
        for (let i = 0; i < this.pages.pages_url.length; i++) {
            selectPageNumber.append(`<option value="${i + 1}">${i + 1}</option>`);
        }
    }

    openPreview() {
        window.location.href = window.reverse('builder:interactive_flyer_settings', this.flyer_id);
    }

    openSettings() {
        window.location.href = window.reverse('builder:interactive_flyer_settings', this.flyer_id) + '?from=true';
    }

    initCategorySelect() {
        const categorySelect = $("#i-product_id_category");
        categorySelect.change(() => {
            let categoryId = categorySelect.val();
            if (categoryId) {
                $.ajax(
                    {
                        method: "GET",
                        url: window.reverse('builder:subcategories_by_category', categoryId)
                    })
                    .done(function (response) {
                        const subcategorySelect = $("#i-product_id_subcategory");
                        subcategorySelect.html(`<option value="">${gettext('Seleziona una sottocategoria')}</option>`);
                        response.forEach((item) => {
                            subcategorySelect.append(`<option value="${item.id}">${item.name}</option>`);
                        });
                        subcategorySelect.prop('disabled', false);
                    })
                    .fail(() => {
                        this.errorMessage();
                    });
            }
        });
    }

    reInitDataTable(tableId) {
        const dtable = $(tableId);
        if ($.fn.dataTable.isDataTable(tableId)) {
            dtable.DataTable().destroy();
        }

        return dtable;
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

    showHideIfChecked(checkBox, idToShowHide) {
        if (checkBox.is(':checked')) {
            $(idToShowHide).removeClass('d-none');
        } else {
            $(`${idToShowHide} input`).val('');
            $(idToShowHide).addClass('d-none');
        }
    }
    // endregion

    // region image cropper
    initImageCropper(new_product, product=null) {
        this.destroyImageCropper();
        this.cropper_item = $('#flyer-page-image');
        var data;
        if (!new_product) {
            const {left, top, width, height} = this.getCoordinatesFromPercentage(product.blueprint);
            data = {
                "x": left,
                "y": top,
                "height": height,
                "width": width,
                "rotate": 0,
                "scaleX": 1,
                "scaleY": 1
            };
        } else {
            const {left, top, width, height} = this.getCoordinatesFromPercentage(this.blueprint);
            this.last_cropper = {
                'top': top,
                'left': left,
                'width': width,
                'height': height
            };
            data = {
                "x": this.last_cropper.left,
                "y": this.last_cropper.top,
                "height": this.last_cropper.height,
                "width": this.last_cropper.width,
                "rotate": 0,
                "scaleX": 1,
                "scaleY": 1
            };
        }

        this.cropper_item.cropper({
            viewMode: 2,
            initialAspectRatio: 1,
            autoCropArea: 0.3,
            movable: false,
            zoomable: false,
            preview: ".crop-preview",
            data: data,
            crop: (event) => {
                $(".blueprint_top").val(event.detail.y);
                $(".blueprint_left").val(event.detail.x);
                $(".blueprint_width").val(event.detail.width);
                $(".blueprint_height").val(event.detail.height);
                this.last_cropper = {
                    'top': event.detail.y,
                    'left': event.detail.x,
                    'width': event.detail.width,
                    'height': event.detail.height
                };
            },
            checkOrientation: false,
            ready: function (event) {
                App.hide_loader();
            }
        });
        this.reactor.dispatchEvent('cropped_image', this.cropper_item);
    }

    destroyImageCropper() {
        if (this.cropper_item) {
            this.cropper_item.cropper("destroy");
        }
        $(".crop-preview").attr("style", "height:250px;");  /* fix per la preview del crop */
    }
    // endregion

    // region check zip
    setGeneratingPolling() {
        setInterval(() => {
            this.checkZipGeneration();
        }, 5000);
    }

    checkZipGeneration() {
        $.ajax(
            {
                method: "GET",
                url: window.reverse('builder:interactive_flyer_zip_generation_status', this.flyer_id)
            })
            .done(function (response) {
                if (response.status === "generated") {
                    window.location.reload();
                }
            })
            .fail(() => {
                this.errorMessage();
            });
    }

    // endregion

    // region page controller
    firstPage() {
        this.page_selected = 1;
        this.changePage();
    }

    lastPage() {
        this.page_selected = this.flyer_pages;
        this.changePage();
    }

    prevPage() {
        if (this.page_selected > 1) {
            this.page_selected--;
            this.changePage();
        }
    }

    nextPage() {
        if (this.page_selected < this.flyer_pages) {
            this.page_selected++;
            this.changePage();
        }
    }

    goToPage(pageNum, obj) {
        App.show_loader();
        this.page_selected = pageNum + 1;
        this.selectPage(obj);
        this.reactor.dispatchEvent('go_to_page', this.page_selected);
        if (this.page_selected === 0) {
            this.indexManagement();
            this.showHideMenuItems('index');
            $('a[title="Cambia posizione pagina"]').attr('onclick','');
        } else {
            this.changePage();
            this.showHideMenuItems('page');
            $('a[title="Cambia posizione pagina"]').attr('onclick','editInteractiveFlyer.changePagePosition()');
        }
    }

    changePage() {
        $("#current-page").html(this.page_selected);
        const pagUrl = this.pages.pages_url[this.page_selected - 1];
        $("#flyer-page-image").attr("src", pagUrl);
        $("#draw image").attr("src", pagUrl).attr("xlink:href", pagUrl);
        this.boxes.html('');
        // disegno i box
        try {
            if (this.productInPages[this.page_selected - 1] === undefined) {
                throw new DOMException();
            }
            var type=''
            $.each(this.productInPages[this.page_selected - 1], (_, value) => {
                if(value.markers[0].type == 'plus'){
                    type='product'
                }else if(value.markers[0].type == 'play'){
                    type='video'
                }
                else if(value.markers[0].type == 'external-link' || value.markers[0].type == 'internal_link'){
                    type='link'
                }
                this.drawRect(value.blueprint, value.id, type);
            });
            App.hide_loader();
            this.cardWithProducts();
        } catch (e) {
            $.ajax(
                {
                    method: "GET",
                    url: window.reverse("builder:get_interactive_flyer_products_page_api", [this.flyer_id, this.page_selected])
                })
                .done((response) => {
                    if (response.success) {
                        this.productInPages[this.page_selected - 1] = [];
                        var type = '';
                        $.each(response.products, (_, value) => {
                            try {
                                this.productInPages[this.page_selected - 1].push(value);
                                if (value.markers[0].type === 'plus') {
                                    type = 'product';
                                } else if (value.markers[0].type === 'play') {
                                    type = 'video';
                                } else if (value.markers[0].type === 'external-link' || value.markers[0].type === 'internal_link') {
                                    type = 'link';
                                }
                                this.drawRect(value.blueprint, value.id, type);
                            } catch (e) {}
                        });
                        this.cardWithProducts();
                    }
                    App.hide_loader();
                })
                .fail(() => {
                    this.errorMessage();
                });
        }
        this.destroyImageCropper();
    }
    // endregion

    // region page management
    deletePage() {
        Swal.fire({
            title: `${gettext('Sei sicuro di voler eliminare la pagina e tutti i prodotti interattivi correlati?')}`,
            showDenyButton: true,
            showCancelButton: false,
            confirmButtonText: `${gettext('Si')}`,
            denyButtonText: `${gettext('Annulla')}`,
        }).then((result) => {
            if (result.isConfirmed) {
                if (this.page_selected === 0){
                    this.deleteFlyerIndex();
                } else {
                    $.ajax(
                        {
                            method: "GET",
                            url: window.reverse("builder:interactive_flyer_delete_page", [this.flyer_id, this.page_selected])
                        })
                        .done((response) => {
                            if (response.success) {
                                /* rimuovi la pagina */
                                this.pages.pages_url.splice(this.page_selected - 1, 1);
                                this.pages.thumbs_url.splice(this.page_selected - 1, 1);
                                /* shifto le interattività */
                                let objLength = Object.keys(this.productInPages).length;
                                for (let j = this.page_selected; j < objLength; j++) {
                                    this.productInPages[j - 1] = this.productInPages[j];
                                }
                                delete this.productInPages[objLength - 1];

                                this.page_selected = 1;
                                this.changePage();
                                this.flyer_pages = this.pages.pages_url.length;
                                $('#total-pages').html(this.flyer_pages);
                                this.initPageBar();
                            }
                        })
                        .fail(() => {
                            this.errorMessage();
                        });
                }
            }
        });
    }

    changePageBackground() {
        if (this.page_selected === 0) {
            this.addIndexModal();
        } else {
            $("#change-page-image-page-number").val(this.page_selected);
            $("#change-page-image-modal").modal("show");
        }
    }

    addPage() {
        $('#add-page-modal').modal('show');
    }

    changePagePosition(){
        $('#change-page-modal').modal('show');
        $("#change-page-number").val(this.page_selected);
    }
    // endregion

    // region left page bar
    initPageBar() {
        var pageBarBody = $('#page-bar-body');
        pageBarBody.html('');
        if (this.pages.index.page_url) {
            let htmlIndex = `<div class="mt-4 text-center cursor-pointer index" onclick="editInteractiveFlyer.goToPage(-1, this);">
                <img src="${this.pages.index.page_url}" height="100px">
                <h5 class="mt-1">${gettext('Indice')}</h5>
            </div>`;
            pageBarBody.append(htmlIndex);
        }
        this.pages.thumbs_url.forEach((url, index) => {
            const isSelected = index === 0 ? 'selected' : '';
            let htmlPage = `<div class="mt-4 text-center cursor-pointer ${isSelected}" onclick="editInteractiveFlyer.goToPage(${index}, this);">
                <img class="mt-1" src="${url}" height="100px">
                <h5 class="mt-1">${index + 1}</h5>
            </div>`;
            pageBarBody.append(htmlPage);
        });
    }
    selectPage(obj) {
        $('#page-bar-body').children('div').each(function () {
            $(this).removeClass('selected');
        });
        $(obj).addClass('selected');
    }
    // endregion

    hideAllCards() {
        this.cards.forEach((cardId) => {
            $(cardId).fadeOut("fast");
        });
    }
    addProductInteraction() {
        if ($('#add-product-card').is(':visible')) {
            Swal.fire({
              title: `${gettext('Potrebbero esserci delle modifiche non salvate, vuoi continuare?')}`,
              showDenyButton: true,
              confirmButtonText: `${gettext('Continua')}`,
              denyButtonText: `${gettext('Annulla')}`,
            }).then((result) => {
              if (result.isConfirmed) {
                  this.undoInteractivity('product', false);
                  setTimeout(() => {
                      $("#add-product-card").fadeIn("slow");
                      $(".create-product-block").first().removeClass("d-none");
                      $(".update-product-block").first().addClass("d-none");
                      this.initImageCropper(true);
                      this.switchPanel('image');
                  }, 500);
              }
            });
        } else {
            this.hideAllCards();
            setTimeout(() => {
                $("#add-product-card").fadeIn("slow");
                $(".create-product-block").first().removeClass("d-none");
                if (!this.pages.has_projects) {
                    $('#if-has-project').addClass('d-none');
                }
                $(".update-product-block").first().addClass("d-none");
                this.initImageCropper(true);
                this.switchPanel('image');
            }, 500);
        }
    }
    // region video interaction
    addVideoInteraction() {
        this.hideAllCards();
        setTimeout(() => {
            $('#i-interaction-video_show_tooltip').on('change', () => {
                this.showHideIfChecked($('#i-interaction-video_show_tooltip'), '#tooltip-interaction-video');
            });
            $(`#interaction-video-form input[value="True"][name="open_modal"]`).prop("checked", true);
            $("#interaction-video-details").removeClass("d-none");
            $("#add-video-card").fadeIn("slow");
            this.initImageCropper(true);
            this.switchPanel('image');

            $('#edit-video').addClass('d-none');
            $('#edit-video').removeClass('d-block');
            $('#radio-add-video').removeClass('d-none');
            $('#radio-add-video').addClass('d-block');
        }, 500);
    }

    editVideoInteractionFromPage(obj) {
        let videoId = obj.getAttribute('attr-video-id');
        const videoIdx = this.searchProductIndex(videoId, 'id');
        this.setVideoInForm(this.productInPages[this.page_selected - 1][videoIdx]);
        $('#edit-video').addClass('d-block');
        $('#radio-add-video').removeClass('d-block');
        $('#radio-add-video').addClass('d-none');
    }

    setVideoInForm(video) {
        this.hideAllCards();
        $('#i-interaction-video_id').val(video.id);

        let marker = {};
        video.markers.forEach((aMarker) => {
           if (aMarker.type === 'play') {
               marker = aMarker;
           }
        });
        if (marker.data.open_modal) {
            $(`#interaction-video-form input[value="True"][name="open_modal"]`).prop("checked", true);
            $('#interaction-video-details').removeClass('d-none');
            if (marker.data.show_icon) {
                $('#i-interaction-video_show_icon').prop('checked', true);
            }
            if (marker.data.tooltip !== '') {
                $('#i-interaction-video_show_tooltip').prop('checked', true);
                $('#i-interaction-video_tooltip').val(marker.data.tooltip);
                $('#tooltip-interaction-video').removeClass('d-none');
            }
        } else {
            $(`#interaction-video-form input[value="False"][name="open_modal"]`).prop("checked", true);
        }
        var link = '';
        const videoPreviewContainer = $('#i-interaction-video-edit-preview');
        videoPreviewContainer.removeClass('d-none');
        if (marker.data.video_type === 'youtube') {
            $('#i-interaction-video-edit-preview div').html(`https://youtube.com/watch/${marker.data.link}`);
        } else if (marker.data.video_type === 'video_file') {
            link = marker.data.link;
            $('#i-interaction-video-edit-preview div').html(link.split("/").pop());
        }

        setTimeout(() => {
            $('#i-interaction-video_show_tooltip').on('change', () => {
                this.showHideIfChecked($('#i-interaction-video_show_tooltip'), '#tooltip-interaction-video');
            });
            $("#add-video-card").fadeIn("slow");
            this.initImageCropper(false, video);
            this.switchPanel('image');
        }, 500);
    }

    videoRadioClick(obj) {
        const radioValue = obj.getAttribute('value');
        switch (radioValue) {
            case 'video_file':
                $('#interaction-video_video_type_vf').removeClass('d-none');
                $('#interaction-video_video_type_yt').addClass('d-none');
                break;

            case 'youtube':
                $('#interaction-video_video_type_vf').addClass('d-none');
                $('#interaction-video_video_type_yt').removeClass('d-none');
                break;
        }
    }

    videoDetailRadioClick(obj) {
        const radioValue = obj.getAttribute('value');
        switch (radioValue) {
            case 'True':
                $('#interaction-video-details').removeClass('d-none');
                break;

            case 'False':
                $('#interaction-video-details').addClass('d-none');
                break;
        }
    }

    saveVideoInteractivity(){
        const interactionType = 'video';
        let urlToSubmit = '/it' + window.reverse('builder:interactive_flyer_interactivity_api', [this.flyer_id, interactionType]);
        const formData = new FormData();
        const formParams = $('#interaction-video-form').serializeArray();
        $('#interaction-video_preview').html('');
        $('#interaction-video_yt_preview iframe').attr('src','');
        let videoType = '';
        
        if ((($('#i-interaction-video_link').text() !== '' && $('#i-interaction-video_video_file').val() !== '') ||
            ($('#i-interaction-video_link').val() !== '' || $('#i-interaction-video_video_file').val() !== '')) || $('#i-interaction-video-edit-preview div').html() != '') {
            $.each(formParams, (i, val) => {
                if (val.name === 'video_type') {
                    videoType = val.value;
                    formData.append(val.name, val.value);
                } else if (val.name === 'id') {
                    if (val.value !== '') {
                        formData.append(val.name, val.value);
                        urlToSubmit = '/it' + window.reverse('builder:interactive_flyer_product_interactivity_api', [this.flyer_id, val.value, interactionType]);
                    }
                } else {
                    formData.append(val.name, val.value);
                }
            });
            let ytUrl = $('#i-interaction-video_link').val();
            let videoElement = $(`#i-interaction-video_video_file`);
            if (videoType === 'video_file') {
                
                // let videoElement = $(`#i-interaction-video_video_file`);
                if (videoElement[0].files.length != 0) {
                    let videoFileData = videoElement[0].files[0];
                    formData.append("video_file", videoFileData);
                // } else if( $('#i-interaction-video-edit-preview div').html() == '' ){
                    
                //     this.errorMessage(`${gettext('Scegli un video da riprodurre')}`);
                //     return;
                } else {
                    this.errorMessage(`${gettext('Scegli un video da riprodurre')}`);
                    return;
                }
            } else if (ytUrl === '' && $('#i-interaction-video-edit-preview div').html() == '' ) {
                this.errorMessage(`${gettext('Scegli un video da riprodurre')}`);
                return;
            }else if($('#i-interaction-video-edit-preview div').html() != '' && (ytUrl == '' || !(videoElement[0].files))){
                formData.append('do-nothing', 'do-nothing');
            }
            if (videoType === 'youtube') {
                try {
                    let ytRegexp = new RegExp("^.*(youtu.be\\/|v\\/|embed\\/|watch\\?|watch\\/|youtube.com\\/user\\/[^#]*#([^\\/]*?\\/)*)\\??v?=?([^#\\&\\?]*).*", "g");
                    let ytmatch = ytRegexp.exec(ytUrl);
                    formData.set('link', ytmatch[3]);
                } catch (e) {
                    this.errorMessage(`${gettext('Scegli un video da riprodurre')}`);
                    return;
                }
            }
            formData.append('active', true);
            this.savePageInteraction(formData, interactionType, urlToSubmit);
        } else {
            this.errorMessage(`${gettext('Scegli un video')}`);
        }
        
    }
    // endregion

    cardWithProducts() {
        this.hideAllCards();
        const products = [], videos = [], internalLinks = [], externalLinks = [];
        $.each(this.productInPages[this.page_selected - 1], (_, item) => {
            switch (item.type) {
                case "internal_link":
                    internalLinks.push(item);
                    break;

                case "external_link":
                    externalLinks.push(item);
                    break;

                case "product":
                    products.push(item);
                    break;

                case "video":
                    videos.push(item);
                    break;
            }
        });

        setTimeout(() => {
            if (products.length > 0) {
                const tableId = '#page-products-table';
                let productsWithBlueprint = [];
                products.forEach((item) => {
                    if (item.blueprint) {
                        let i = 0;
                        products.forEach((item2) => {
                            if (item2.codice_interno_insegna == item.codice_interno_insegna) {
                                i++;
                            }
                        });
                        if (i > 1) {
                            item["expandible"] = true;
                        }
                        productsWithBlueprint.push(item);
                    }
                });
                const dtable = this.reInitDataTable(tableId);
                dtable.DataTable({
                    rowId: 'id',
                    language: {
                        url: '/static/gull-admin/js/plugins/localization/italian.json'
                    },
                    searching: false,
                    paging: false,
                    data: productsWithBlueprint,
                    order: [[ 2, "desc" ]],
                    columns: [
                        {
                            "className":      'dt-control',
                            "orderable":      false,
                            "data":           null,
                            render: function (data, type, row) {
                                if (data.expandible) {
                                    return `<i class="nav-icon i-Add"></i>`;
                                } else {
                                    return '';
                                }
                            },
                        },
                        {data: 'id', "visible": false, orderable: false},
                        {
                            data: null,
                            orderable: false,
                            render: function (data, type, row) {
                                for (let i = 0; i < data.images.length; i++){
                                    if (data.images[i].cropped) {
                                        return `<img src="${data.images[i].image_file}"/>`;
                                    }
                                }
                                return '';
                            }
                        },
                        {data: 'field1'},
                        {
                            data: function (data, type, row) {
                               return `<span class="product-categories">${data.category}</span><p class="product-categories">${data.subcategory}</p>`;
                            }
                        },
                        {data: 'price_label'},
                        {
                            data: null,
                            render: function (data, type, row) {
                                var array_interactivities = {
                                    'world':`<div class="d-inline">
                                        <svg class="mr-1" xmlns="http://www.w3.org/2000/svg" height="15px" viewBox="0 0 24 24" width="15px" fill="#00000"><path d="M0 0h24v24H0z" fill="none"></path>
                                            <path d="M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zm6.93 6h-2.95c-.32-1.25-.78-2.45-1.38-3.56 1.84.63 3.37 1.91 4.33 3.56zM12 4.04c.83 1.2 1.48 2.53 1.91 3.96h-3.82c.43-1.43 1.08-2.76 1.91-3.96zM4.26 14C4.1 13.36 4 12.69 4 12s.1-1.36.26-2h3.38c-.08.66-.14 1.32-.14 2 0 .68.06 1.34.14 2H4.26zm.82 2h2.95c.32 1.25.78 2.45 1.38 3.56-1.84-.63-3.37-1.9-4.33-3.56zm2.95-8H5.08c.96-1.66 2.49-2.93 4.33-3.56C8.81 5.55 8.35 6.75 8.03 8zM12 19.96c-.83-1.2-1.48-2.53-1.91-3.96h3.82c-.43 1.43-1.08 2.76-1.91 3.96zM14.34 14H9.66c-.09-.66-.16-1.32-.16-2 0-.68.07-1.35.16-2h4.68c.09.65.16 1.32.16 2 0 .68-.07 1.34-.16 2zm.25 5.56c.6-1.11 1.06-2.31 1.38-3.56h2.95c-.96 1.65-2.49 2.93-4.33 3.56zM16.36 14c.08-.66.14-1.32.14-2 0-.68-.06-1.34-.14-2h3.38c.16.64.26 1.31.26 2s-.1 1.36-.26 2h-3.38z"></path>
                                        </svg>
                                            </div>`,
                                    'play':`<div class="d-inline">
                                            <svg class="mr-1" xmlns="http://www.w3.org/2000/svg" fill="#00000" height="15px" width="15px" viewBox="0 0 24 24"><path d="M0 0h24v24H0z" fill="none"></path>
                                            <path d="M8 5v14l11-7z"></path>
                                        </svg>
                                    </div>`,
                                    'hat-chef':`<div class="d-inline">
                                                    <svg class="mr-1" xmlns="http://www.w3.org/2000/svg" height="15px" viewBox="0 0 24 24" width="15px" fill="#00000">
                                                    <path d="M0 0h24v24H0V0z" fill="none"></path>
                                                    <path d="M8.1 13.34l2.83-2.83L3.91 3.5c-1.56 1.56-1.56 4.09 0 5.66l4.19 4.18zm6.78-1.81c1.53.71 3.68.21 5.27-1.38 1.91-1.91 2.28-4.65.81-6.12-1.46-1.46-4.2-1.1-6.12.81-1.59 1.59-2.09 3.74-1.38 5.27L3.7 19.87l1.41 1.41L12 14.41l6.88 6.88 1.41-1.41L13.41 13l1.47-1.47z"></path>
                                                </svg>
                                            </div>`,
                                    'info':`<div class="d-inline">
                                            <svg class="mr-1" xmlns="http://www.w3.org/2000/svg" height="15px" viewBox="0 0 24 24" width="15px" fill="#00000">
                                            <path d="M0 0h24v24H0z" fill="none"></path>
                                            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"></path>
                                        </svg>
                                    </div>`,
                                    'specs':`<div class="d-inline">
                                                    <svg class="mr-1" xmlns="http://www.w3.org/2000/svg" height="18px" viewBox="0 0 24 24" width="18px" fill="#00000"><path d="M0 0h24v24H0z" fill="none"></path>
                                                    <path d="M19 5v14H5V5h14m1.1-2H3.9c-.5 0-.9.4-.9.9v16.2c0 .4.4.9.9.9h16.2c.4 0 .9-.5.9-.9V3.9c0-.5-.5-.9-.9-.9zM11 7h6v2h-6V7zm0 4h6v2h-6v-2zm0 4h6v2h-6zM7 7h2v2H7zm0 4h2v2H7zm0 4h2v2H7z"></path>
                                                </svg>
                                            </div>`

                                };

                                if (data.markers.length <= 1){
                                    return '';
                                } else {
                                    var interactivities = '';
                                    for (let i=1; i < data.markers.length ; i++){
                                       interactivities = interactivities + array_interactivities[data.markers[i].type];
                                    }
                                    return interactivities;
                                }
                            }
                        },
                        {
                            data: null,
                            orderable: false,
                            render: function (data, type, row) {
                                return `<button title="Modifica" class="btn btn-secondary btn-sm d-block mb-1" attr-product-id="${row.id}"
                                            onclick="editInteractiveFlyer.editProductFromPage(this);"
                                            ><i _ngcontent-dkh-c8="" class="text-15 i-Pen-5"></i></button>
                                        <button title="Cancella" class="btn btn-danger btn-sm d-block button-delete" attr-product-id="${row.id}"
                                            onclick="deleteElement(this,'prodotto');"
                                            >
                                            <svg class="svg-delete" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 448 512"><defs><style>.cls-1{fill:#fff;}</style></defs><g id="Livello_2" data-name="Livello 2"><g id="Livello_1-2" data-name="Livello 1"><path class="cls-1" d="M432,32H312l-9.4-18.7A24,24,0,0,0,281.1,0H166.8a23.72,23.72,0,0,0-21.4,13.3L136,32H16A16,16,0,0,0,0,48V80A16,16,0,0,0,16,96H432a16,16,0,0,0,16-16V48A16,16,0,0,0,432,32ZM53.2,467a48,48,0,0,0,47.9,45H346.9a48,48,0,0,0,47.9-45L416,128H32Z"/></g></g></svg>
                                            </button>`;
                            }
                        }
                    ]
                });
                $('#page-products-table tbody').on('click', 'td.dt-control', (event) => {
                    const datable = $('#page-products-table').DataTable();
                    var tr = $(event.currentTarget).closest('tr');
                    const aProductId = tr.attr("id");
                    var row = datable.row(tr);
                    if (row.child.isShown()) {
                        row.child.hide();
                        tr.find('i').addClass("i-Add").removeClass("i-Remove");
                    } else {
                        const related = []
                        const idxProduct = this.searchProductIndex(aProductId, 'id');
                        let aProduct = this.productInPages[this.page_selected - 1][idxProduct];
                        products.forEach((item3) => {
                            if (item3.codice_interno_insegna == aProduct.codice_interno_insegna && aProductId != item3.id) {
                                related.push(item3);
                            }
                        });
                        if (related.length > 0) {
                            let childTableHtml = "<table class='w-100'>";
                            related.forEach((rel) => {
                                childTableHtml += `<tr>`;
                                childTableHtml += `<td>${rel.field1}</td>`;
                                childTableHtml += `<td><button title="Modifica" class="btn btn-secondary btn-sm d-block mb-1" attr-product-id="${rel.id}"
                                        onclick="editInteractiveFlyer.editProductFromPage(this);"
                                        ><i _ngcontent-dkh-c8="" class="text-15 i-Pen-5"></i></button>
                                    <button title="Cancella" class="btn btn-danger btn-sm d-block button-delete" attr-product-id="${rel.id}"
                                        onclick="deleteElement(this,'prodotto');"
                                        >
                                        <svg class="svg-delete" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 448 512"><defs><style>.cls-1{fill:#fff;}</style></defs><g id="Livello_2" data-name="Livello 2"><g id="Livello_1-2" data-name="Livello 1"><path class="cls-1" d="M432,32H312l-9.4-18.7A24,24,0,0,0,281.1,0H166.8a23.72,23.72,0,0,0-21.4,13.3L136,32H16A16,16,0,0,0,0,48V80A16,16,0,0,0,16,96H432a16,16,0,0,0,16-16V48A16,16,0,0,0,432,32ZM53.2,467a48,48,0,0,0,47.9,45H346.9a48,48,0,0,0,47.9-45L416,128H32Z"/></g></g></svg>
                                        </button></td>`;
                                childTableHtml += `</tr>`;
                            });
                            childTableHtml += "</table>";
                            row.child(childTableHtml).show();
                            tr.find('i').removeClass("i-Add").addClass("i-Remove");
                        }
                    }
                });
                $("#page-products-card").fadeIn("slow");
            }

            if (videos.length > 0) {
                const tableId = '#video-interactivities-table';
                const dtable = this.reInitDataTable(tableId);
                dtable.DataTable({
                    language: {
                        url: '/static/gull-admin/js/plugins/localization/italian.json'
                    },
                    searching: false,
                    paging: false,
                    data: videos,
                    order: [[ 1, "desc" ]],
                    columns: [
                        {data: 'id', "visible": false},
                        {
                            data: null,
                            render: function (data, type, row) {
                                for (let i = 0; i < row.images.length; i++){
                                    if (row.images[i].cropped) {
                                        return `<img src="${row.images[i].image_file}"/>`;
                                    }
                                }
                                return '';
                            }
                        },
                        {
                            data: null,
                            render: function (data, type, row) {
                                if(row.markers[0].data.video_type === "youtube"){
                                    return 'https://youtube.com/watch/'+row.markers[0].data.link;
                                }else{
                                    return row.markers[0].data.link.split("/").pop();
                                }
                                
                            }
                        },
                        {
                            data: null,
                            render: function (data, type, row) {
                                var icon='';
                                if(row.markers[0].data.video_type == "youtube"){
                                    icon='<i _ngcontent-dyj-c8="" class="text-20 i-Youtube"></i>';
                                }else{
                                    icon='<i _ngcontent-dyj-c8="" class="text-20 i-Start-2"></i>';
                                }
                                return icon;
                            }
                        },
                        
                        {
                            data: null,
                            render: function (data, type, row) {
                                return `<button title="Modifica" class="btn btn-secondary btn-sm" attr-video-id="${row.id}"
                                             onclick="editInteractiveFlyer.editVideoInteractionFromPage(this);"
                                            >
                                            <i _ngcontent-dkh-c8="" class="text-15 i-Pen-5"></i>
                                            </button>
                                        <button title="Cancella" class="btn btn-danger btn-sm button-delete" attr-product-id="${row.id}"
                                            onclick="deleteElement(this,'video');"
                                            >
                                            <svg class="svg-delete" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 448 512"><defs><style>.cls-1{fill:#fff;}</style></defs><g id="Livello_2" data-name="Livello 2"><g id="Livello_1-2" data-name="Livello 1"><path class="cls-1" d="M432,32H312l-9.4-18.7A24,24,0,0,0,281.1,0H166.8a23.72,23.72,0,0,0-21.4,13.3L136,32H16A16,16,0,0,0,0,48V80A16,16,0,0,0,16,96H432a16,16,0,0,0,16-16V48A16,16,0,0,0,432,32ZM53.2,467a48,48,0,0,0,47.9,45H346.9a48,48,0,0,0,47.9-45L416,128H32Z"/></g></g></svg>
                                            </button>`;
                            }
                        }
                    ]
                });
                $("#video-interactivities-card").fadeIn("slow");
            }
            if (internalLinks.length > 0) {
                const tableId = '#internal-link-interactivities-table';
                const dtable = this.reInitDataTable(tableId);

                dtable.DataTable({
                    language: {
                        url: '/static/gull-admin/js/plugins/localization/italian.json'
                    },
                    searching: false,
                    paging: false,
                    data: internalLinks,
                    order: [[ 1, "desc" ]],
                    columns: [
                        {data: 'id', "visible": false},
                       
                        {
                            data: null,
                            render: function (data, type, row) {
                                for (let i = 0; i < row.images.length; i++){
                                    if (row.images[i].cropped) {
                                        return `<img src="${row.images[i].image_file}"/>`;
                                    }
                                }
                                return '';
                            }
                        },
                        {
                            data: null,
                            render: function (data, type, row) {
                                return row.markers[0].data.page_number;
                            }
                        },
                        {
                            data: null,
                            render: function (data, type, row) {
                                return `<button title="Modifica" class="btn btn-secondary btn-sm" attr-link-id="${row.id}"
                                             onclick="editInteractiveFlyer.editInternalLinkInteractionFromPage(this);"
                                             >
                                             <i _ngcontent-dkh-c8="" class="text-15 i-Pen-5"></i>
                                             </button>
                                        <button title="Cancella" class="btn btn-danger btn-sm button-delete" attr-product-id="${row.id}"
                                            onclick="deleteElement(this,'link interno');"
                                            >
                                            <svg class="svg-delete" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 448 512"><defs><style>.cls-1{fill:#fff;}</style></defs><g id="Livello_2" data-name="Livello 2"><g id="Livello_1-2" data-name="Livello 1"><path class="cls-1" d="M432,32H312l-9.4-18.7A24,24,0,0,0,281.1,0H166.8a23.72,23.72,0,0,0-21.4,13.3L136,32H16A16,16,0,0,0,0,48V80A16,16,0,0,0,16,96H432a16,16,0,0,0,16-16V48A16,16,0,0,0,432,32ZM53.2,467a48,48,0,0,0,47.9,45H346.9a48,48,0,0,0,47.9-45L416,128H32Z"/></g></g></svg>
                                            </button>`;
                            }
                        }
                    ]
                });
                $("#internal-link-interactivities-card").fadeIn("slow");
            }
            if (externalLinks.length > 0) {
                const tableId = '#external-link-interactivities-table';
                const dtable = this.reInitDataTable(tableId);
                dtable.DataTable({
                    language: {
                        url: '/static/gull-admin/js/plugins/localization/italian.json'
                    },
                    searching: false,
                    paging: false,
                    data: externalLinks,
                    order: [[ 1, "desc" ]],
                    columns: [
                        {data: 'id', "visible": false},
                        {
                            data: null,
                            render: function (data, type, row) {
                                for (let i = 0; i < row.images.length; i++){
                                    if (row.images[i].cropped) {
                                        return `<img src="${row.images[i].image_file}"/>`;
                                    }
                                }
                                return '';
                            }
                        },
                        {
                            data: null,
                            render: function (data, type, row) {
                                
                                var array_interactivities={
                                    'url':`<div class="d-inline">
                                        <svg class="mr-1" xmlns="http://www.w3.org/2000/svg" height="15px" viewBox="0 0 24 24" width="15px" fill="#00000"><path d="M0 0h24v24H0z" fill="none"></path>
                                            <path d="M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zm6.93 6h-2.95c-.32-1.25-.78-2.45-1.38-3.56 1.84.63 3.37 1.91 4.33 3.56zM12 4.04c.83 1.2 1.48 2.53 1.91 3.96h-3.82c.43-1.43 1.08-2.76 1.91-3.96zM4.26 14C4.1 13.36 4 12.69 4 12s.1-1.36.26-2h3.38c-.08.66-.14 1.32-.14 2 0 .68.06 1.34.14 2H4.26zm.82 2h2.95c.32 1.25.78 2.45 1.38 3.56-1.84-.63-3.37-1.9-4.33-3.56zm2.95-8H5.08c.96-1.66 2.49-2.93 4.33-3.56C8.81 5.55 8.35 6.75 8.03 8zM12 19.96c-.83-1.2-1.48-2.53-1.91-3.96h3.82c-.43 1.43-1.08 2.76-1.91 3.96zM14.34 14H9.66c-.09-.66-.16-1.32-.16-2 0-.68.07-1.35.16-2h4.68c.09.65.16 1.32.16 2 0 .68-.07 1.34-.16 2zm.25 5.56c.6-1.11 1.06-2.31 1.38-3.56h2.95c-.96 1.65-2.49 2.93-4.33 3.56zM16.36 14c.08-.66.14-1.32.14-2 0-.68-.06-1.34-.14-2h3.38c.16.64.26 1.31.26 2s-.1 1.36-.26 2h-3.38z"></path>
                                        </svg>
                                            </div>`,
                                    'email':`<div class="d-inline">
                                        <svg xmlns="http://www.w3.org/2000/svg" height="15px" viewBox="0 0 24 24" width="15px" fill="#000000"><path d="M0 0h24v24H0V0z" fill="none"/><path d="M22 6c0-1.1-.9-2-2-2H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6zm-2 0l-8 4.99L4 6h16zm0 12H4V8l8 5 8-5v10z"/>
                                        </svg>
                                    </div>`,
                                    'telephone':`<div class="d-inline">
                                    <svg xmlns="http://www.w3.org/2000/svg" height="15px" viewBox="0 0 24 24" width="15px" fill="#000000"><path d="M0 0h24v24H0V0z" fill="none"/><path d="M6.54 5c.06.89.21 1.76.45 2.59l-1.2 1.2c-.41-1.2-.67-2.47-.76-3.79h1.51m9.86 12.02c.85.24 1.72.39 2.6.45v1.49c-1.32-.09-2.59-.35-3.8-.75l1.2-1.19M7.5 3H4c-.55 0-1 .45-1 1 0 9.39 7.61 17 17 17 .55 0 1-.45 1-1v-3.49c0-.55-.45-1-1-1-1.24 0-2.45-.2-3.57-.57-.1-.04-.21-.05-.31-.05-.26 0-.51.1-.71.29l-2.2 2.2c-2.83-1.45-5.15-3.76-6.59-6.59l2.2-2.2c.28-.28.36-.67.25-1.02C8.7 6.45 8.5 5.25 8.5 4c0-.55-.45-1-1-1z"/>
                                    </svg>
                                            </div>`,
                                    

                                }
                                var interactivities=''
                                if (data.markers.length <= 0){
                                   
                                    return ''
                                    
                                }else{
                                    
                                    for (let i=0; i < data.markers.length ; i++){
                                      
                                       interactivities= interactivities + array_interactivities[data.markers[i].data.link_type]
                                    }
                                    return interactivities;
                                }
                            }
                        },
                        {
                            data: null,
                            render: function (data, type, row) {
                                var link=''
                                if (data.markers.length <= 0){
                                   
                                    return ''
                                    
                                }else{
                                    
                                    for (let i=0; i < data.markers.length ; i++){
                                      
                                        link=`<span class="product-categories">`+ link + data.markers[i].data.link +'</span>'
                                       return link;
                                    }
                                    
                                }
                            }
                        },
                        {
                            data: null,
                            render: function (data, type, row) {
                                return `<button class="btn btn-secondary btn-sm " attr-link-id="${row.id}"
                                             onclick="editInteractiveFlyer.editExternalLinkInteractionFromPage(this);"
                                             title="Modifica">
                                                <i _ngcontent-dkh-c8="" class="text-15 i-Pen-5"></i>
                                             </button>
                                        <button class="btn btn-danger btn-sm button-delete" attr-product-id="${row.id}"
                                            onclick="deleteElement(this, 'link esterno');"
                                            title="Cancella">
                                            <svg class="svg-delete" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 448 512"><defs><style>.cls-1{fill:#fff;}</style></defs><g id="Livello_2" data-name="Livello 2"><g id="Livello_1-2" data-name="Livello 1"><path class="cls-1" d="M432,32H312l-9.4-18.7A24,24,0,0,0,281.1,0H166.8a23.72,23.72,0,0,0-21.4,13.3L136,32H16A16,16,0,0,0,0,48V80A16,16,0,0,0,16,96H432a16,16,0,0,0,16-16V48A16,16,0,0,0,432,32ZM53.2,467a48,48,0,0,0,47.9,45H346.9a48,48,0,0,0,47.9-45L416,128H32Z"/></g></g></svg>
                                            </button>`;
                            }
                        }
                    ]
                });

                $("#external-link-interactivities-card").fadeIn("slow");
            }
        }, 300);
    }

    switchPanel(panel) {
        const boxesContainer = $('#draw');
        if (panel === 'image') {
            boxesContainer.addClass('d-none');
        } else if (panel === 'svg') {
            boxesContainer.removeClass('d-none');
        }
    }

    undoInteractivity(form='product', showProductsCard=true) {
        // this.destroyImageCropper();
        this.hideAllCards();
        if (form === 'product') {
            // resetto form prodotti start
            $("#reset-product-form").click();
            // $("#i-product-form fieldset").attr('disabled', 'disabled');
            $("#i-product_varieties").tagging("removeAll");
            for (const elemnt of $("#i-product-form input[type='checkbox']")) {
                $(elemnt).removeAttr('checked');
            }
            $(".create-product-block").first().addClass("d-none");
            $(".update-product-block").first().addClass("d-none");
            $("#i-product_id_subcategory").html('').attr('disabled', 'disabled');
            // resetto form prodotti end
            this.reactor.dispatchEvent('release_interactivity_product');
        }
        if (form === 'video') {
            $('#interaction-video_preview').html('');
            $('#interaction-video_yt_preview iframe').attr('src','');
            $('#interaction-video-form')[0].reset();
            $('#interaction-video-details').addClass('d-none');
            $('#interaction-video_video_type_vf').addClass('d-none');
            $('#interaction-video_video_type_yt').addClass('d-none');
            $('#tooltip-interaction-video').addClass('d-none');
            $('#i-interaction-video-edit-preview').addClass('d-none');
        }
        if (form === 'external_link') {
            $('#i-external-link-form')[0].reset();
            $('#i-external-link_link_email_wrapper').addClass('d-none');
            $('#i-external-link_link_url_wrapper').addClass('d-none');
            $('#i-external-link_link_telephone_wrapper').addClass('d-none');
            $('#tooltip-external-link').addClass('d-none');
        }
        if (form === 'internal_link') {
            $('#i-internal-link-form')[0].reset();
            $('#tooltip-internal-link').addClass('d-none');
        }
        if (form === 'internal_link_index') {
            $('#i-internal-link-index-form')[0].reset();
            this.switchPanel('svg');
            this.cardIndex();
        }
        if (form === 'external_link_index') {
            $('#i-external-link-index-form')[0].reset();
            this.switchPanel('svg');
            this.cardIndex();
        }

        if (showProductsCard) {
            this.switchPanel('svg');
            this.cardWithProducts();
        }
        this.destroyImageCropper();
    }

    getCoordinatesFromPercentage(data) {
        return {
            'left': data.left * this.flyerDimensions.width / 100,
            'top': data.top * this.flyerDimensions.height / 100,
            'width': data.width * this.flyerDimensions.width / 100,
            'height': data.height * this.flyerDimensions.height / 100
        };
    }
    drawRect(data, id=0, type='product') {
        let rect = document.createElement('div');
        rect.setAttribute('class', 'interactivity-box ');
        rect.setAttribute(
            'style',
            `width: ${data.width + ''}%;
             height: ${data.height+  ''}%; 
             top: ${data.top + ''}%; 
             left: ${data.left + ''}%;`,
             ); 
             
        rect.setAttribute(
            'onclick',
            `open_detail(${id} , '${type}')`
        )
        this.boxes.append(rect);
    }

    selectProductFromProject() {
        $.ajax({
            method: "GET",
            url: window.reverse('builder:interactive_flyer_project_items', this.flyer_id)
        })
            .done(function (data) {
                const itemsTable = $('#items-table');
                itemsTable.DataTable().destroy();
                itemsTable.DataTable({
                    language: {
                        url: '/static/gull-admin/js/plugins/localization/italian.json'
                    },
                    data: data,
                    columns: [
                        {data: 'codice_interno_insegna'},
                        {data: 'field1'},
                        {data: 'field2'},
                        {data: 'field3'},
                        {data: 'field4'},
                        {
                            data: null,
                            render: function (data, type, row) {
                                return `<button class="btn btn-secondary btn-sm" attr-product-id="${row.product_uid}"
                                    onclick="editInteractiveFlyer.productSelectedFromProject(this);"
                                    >${gettext('Seleziona')}</button>`;
                            }
                        }
                    ]
                });
                $('#project-items-modal').modal('show');
            })
            .fail(() => {
                this.errorMessage();
            });
    }

    selectProductFromArchive() {
        $.ajax({
            method: "GET",
            url: window.reverse('builder:interactive_flyer_archive_products', this.flyer_id)
        })
            .done(function (data) {
                const itemsTable = $('#items-table');
                itemsTable.DataTable().destroy();
                itemsTable.DataTable({
                    language: {
                        url: '/static/gull-admin/js/plugins/localization/italian.json'
                    },
                    data: data,
                    columns: [
                        {data: 'codice_interno_insegna'},
                        {data: 'field1'},
                        {data: 'field2'},
                        {data: 'field3'},
                        {data: 'field4'},
                        {
                            data: null,
                            render: function (data, type, row) {
                                return `<button class="btn btn-secondary btn-sm" attr-product-id="${row.product_uid}"
                                            onclick="editInteractiveFlyer.productSelectedFromArchive(this);"
                                            >${gettext('Seleziona')}</button>`;
                            }
                        }
                    ]
                });
                $('#project-items-modal').modal('show');
            })
            .fail(() => {
                this.errorMessage();
            });
    }

    productSelectedFromProject(obj) {
        let productId = obj.getAttribute('attr-product-id');
        $('#project-items-modal').modal('hide');
        App.show_loader("#i-product-form");
        $.ajax({
            method: "GET",
            url: window.reverse('builder:get_product_campaign_api', [this.flyer_id, productId])
        })
            .done((data) => {
                $("#i-product-form fieldset").removeAttr('disabled');
                this.setProductInForm(data);
            })
            .fail(() => {
                this.errorMessage();
            })
            .always(function () {
                App.hide_loader("#i-product-form");
            });
    }

    productSelectedFromArchive(obj) {
        let productId = obj.getAttribute('attr-product-id');
        $('#project-items-modal').modal('hide');
        App.show_loader("#i-product-form");
        $.ajax({
            method: "GET",
            url: window.reverse('builder:get_product_archive_api', productId)
        })
            .done((data) => {
                $("#i-product-form fieldset").removeAttr('disabled');
                this.setProductInForm(data);
            })
            .fail(() => {
                this.errorMessage();
            })
            .always(function () {
                App.hide_loader("#i-product-form");
            });
    }

    setProductInForm(data, newProduct=true) {
        $('#i-product-form').attr('new-product', newProduct);
        for (const [key, value] of Object.entries(data)) {
            let categoryFix = '';
            const key2 = key.replaceAll('_id', '');
            if (!newProduct && (key === 'category_id' || key === 'subcategory_id')) {
                categoryFix = 'id_';
            }
            const elmnt = $(`#i-product_${categoryFix}${key2}`);
            if (elmnt.hasClass('tagBox')) {
                elmnt.tagging( "add", value);
            } else if (elmnt.hasClass('textinput')) {
                elmnt.val(value);
            } else if (elmnt.attr('type') === 'checkbox' && value) {
                elmnt.attr('checked', false);
                if(typeof(value) === "boolean") {
                    if (value) {
                        elmnt.attr('checked', 'checked');
                    }
                } else if (value >= 0) {
                    elmnt.attr('checked', 'checked');
                }
            } else if (elmnt.is('select')) {
                if ((newProduct && key === 'id_category') || (!newProduct && key === 'category_id')) {
                    $(`#i-product_${categoryFix}${key2} option[value="${value}"]`).prop('selected', true);
                    elmnt.change();
                }
                if ((newProduct && key === 'id_subcategory') || (!newProduct && key === 'subcategory_id')) {
                    let count = 0;
                    const intervalSubcategory = setInterval(() => {
                        $(`#i-product_${categoryFix}${key2} option[value="${value}"]`).prop('selected', true);
                        count++;
                        var elmntString = ''
                        if(elmnt.val() == null) {
                            var elmntString = 'null' 
                        }else {
                            elmntString = elmnt.val().toString()
                        }
                        if (count > 5 || elmntString === value.toString()) {
                            clearInterval(intervalSubcategory);
                        }
                    }, 500);
                } else {
                    $(`#i-product_${key} option[value="${value}"]`).prop('selected', true);
                    elmnt.change();
                }
            }else if(key == 'weight_unit_of_measure') {
                $('#basic-addon2').val(value);
                if(value == 'ml') {
                    $('#price_for').html('€/l')
                }else {
                    $('#price_for').html('€/kg')
                }
            } else {
                if (key === 'price') {
                    $(`#i-product_price_with_iva`).val(value);
                }
            }
            
        }
    }

    saveProductTriggerEvent(modify) {
        this.reactor.dispatchEvent('save_product', modify);
    }

    saveProduct(modify) {
        App.show_loader();
        this.cropper_item.cropper("getCroppedCanvas").toBlob((blob) => {
            let urlToSubmit = '/it' + window.reverse('builder:interactive_flyer_create_product', this.flyer_id);
            const formData = new FormData();
            const formParams = $('#i-product-form').serializeArray();
            $.each(formParams, (i, val) => {
                if (val.name === 'id') {
                    if (val.value !== '') {
                        formData.append(val.name, val.value);
                        urlToSubmit = '/it' + window.reverse('builder:interactive_flyer_update_product', [this.flyer_id, val.value]);
                    }
                } else {
                    formData.append(val.name, val.value);
                }
            });
            
            const tags = $("#i-product_varieties").tagging("getTags");
            formData.append('weight_unit_of_measure', $('#basic-addon2').val());
            formData.append('varieties', tags.join());
            formData.append('cropped_image', blob, "cropped_image.png");
            formData.append('page', this.page_selected);
            formData.append('modify', modify);
            $.ajax({
                method: "POST",
                url: urlToSubmit,
                data: formData,
                contentType: false,
                processData: false,

            })
                .done((data) => {
                    this.reactor.dispatchEvent('post_save_product', data);
                })
                .fail((data) => {
                    this.errorMessage();
                })
                .always(() => {
                    App.hide_loader();
                    this.reactor.dispatchEvent('release_interactivity_product');
                });
        });
    }

    searchProductIndex(productId, fieldToCompare='id') {
        productId = productId + '';
        let productIndex = -1;
        for (let i = 0; i < this.productInPages[this.page_selected - 1].length; i++) {
            const pId = this.productInPages[this.page_selected - 1][i][fieldToCompare] + '';
            if (pId === productId) {
                productIndex = i;
            }
        }
        return productIndex;
    }

    deleteProductFromPage(obj) {
        App.show_loader();
        let productId = obj.getAttribute('attr-product-id');
        $.ajax({
            method: "GET",
            url: window.reverse('builder:interactive_flyer_delete_product', [this.flyer_id, productId])
        })
            .done((data) => {
                if (data.status === 'deleted') {
                    const productIndex = this.searchProductIndex(productId, 'id');
                    if (productIndex >= 0) {
                        this.productInPages[this.page_selected -1].splice(productIndex, 1);
                        this.changePage();
                    }
                }
            })
            .fail(() => {
                this.errorMessage();
            })
            .always(function () {
                App.hide_loader();
            });
    }

    editProductFromPage(obj) {
        let productId = '';
        if(obj.id) {
            productId = obj.id;
            $('#attr-product-id').attr('value', productId);
        } else {
            productId = obj.getAttribute('attr-product-id');
            $('#attr-product-id').attr('value', productId);
        }

        const productIndex = this.searchProductIndex(productId, 'id');
        const product = this.productInPages[this.page_selected - 1][productIndex];
        this.setProductInForm(product, false);
        this.showProductInteractionInPage(product.markers);
        let counter_image = 0;
        $.each(product.images, (_, image) => {
            if (image.cropped === false) {
                counter_image++;
            }
        });
        $('#number-images').html('<p class="mb-0">Sono presenti <span id="counter-images">'+ counter_image +'</span> immagini/e.');
        this.updateImageCarousel(product.images);
        $("#i-product-form fieldset").removeAttr('disabled');
        this.reactor.dispatchEvent('limit_interactivity_product', product.markers);
        this.hideAllCards();
        setTimeout(() => {
            $("#add-product-card").fadeIn("slow");
            $(".update-product-block").first().removeClass("d-none");
            $(".create-product-block").first().addClass("d-none");
            if (!this.pages.has_projects) {
                $('#if-has-project').addClass('d-none');
            }
            this.initImageCropper(false, product);
            this.switchPanel('image');
            $('#add-product-card').animate({scrollTop:(0)}, 500);
        }, 500);
    }

    // region image management
    imageManagement(obj) {
        let productId = $('#attr-product-id').attr('value');
        $("#product-images-modal").modal("show");
        const imagesWrapper = $('#other-images-wrapper');
        imagesWrapper.addClass('d-none');
        $.ajax({
            method: "GET",
            url: window.reverse('builder:get_interactive_flyer_product_images_api', [this.flyer_id, productId])
        })
            .done((data) => {
                this.updateImageCarousel(data);
                const imagesContainer = $('#other-images-container');
                imagesContainer.html('');
                $.each(data, (_, an_image) => {
                    if (!an_image.cropped) {
                        let htmlBlock = `<div class="col-4" id="oth-img-${an_image.pk}">
                            <img src="${an_image.image_file}" class="img-fluid">
                                <button attr-image-id="${an_image.pk}" attr-product-id="${productId}" class="btn btn-danger btn-block mb-1 mt-1"
                                        onclick="editInteractiveFlyer.deleteProductImage(this);">${gettext('Cancella')}</button>
                        </div>`;
                        imagesContainer.append(htmlBlock);
                        imagesWrapper.removeClass('d-none');
                    }
                });
            })
            .fail((data) => {
                alert(data)
                // this.errorMessage();
            });
    }
    updateImageCarousel(obj){
        $('#carouselExampleControls').html('');
        $.each(obj, (_, image) => {
            if(image.cropped === false){
                if(_ === 0){
                    $('#carouselExampleControls').prepend(
                        ` <div class="carousel-item active" id="`+image.pk+`-img">
                                    <img class="d-block  available-images" src="`+ image.image_file +`" alt="`+_+` slide"  >
                            </div> `
                    );
                }else{
                    $('#carouselExampleControls').prepend(
                        ` <div class="carousel-item " id="`+image.pk+`-img">
                                    <img class="d-block available-images "  src="`+ image.image_file +`" alt="`+_+` slide" >
                            </div> `
                    );
                }
            }
        });
        if(obj.length == 2){
            setTimeout(function(){
                $('.carousel-control-prev').css('display','none');
                $('.carousel-control-next').css('display','none');
            },1000)
            
        }
        
        $('#carouselExampleControls').append(
            `<a class="carousel-control-prev" href="#carouselExampleControls" role="button" data-slide="prev">
                <span class="carousel-control-prev-icon bg-primary" aria-hidden="true"></span>
                <span class="sr-only">Previous</span>
            </a>
            <a class="carousel-control-next" href="#carouselExampleControls" role="button" data-slide="next">
                <span class="carousel-control-next-icon bg-primary" aria-hidden="true"></span>
                <span class="sr-only">Next</span>
            </a>`
        );
    }

    uploadProductImage(obj) {
        let productId = $('#attr-product-id').attr('value');
        $("#product-images-modal").modal("hide");
        App.show_loader();
        var file_data = $("#new_product_image")[0].files[0];
        if (!file_data) {
            App.hide_loader();
            this.errorMessage(`${gettext('Hai dimenticato di inserire l\'immagine')}`);
            return;
        }
        var form_data = new FormData();
        form_data.append("image", file_data);
        $.ajax({
            method: "POST",
            url:  '/it' + window.reverse('builder:interactive_flyer_create_product_image_api', [this.flyer_id, productId]),
            contentType: false,
            processData: false,
            data: form_data,
        })
            .done((data) => {
                if (data.status === 'created') {
                    // <P>
                    this.imageManagement(obj);
                    var counter_images=$('#counter-images').text();
                    counter_images= parseInt(counter_images) + 1 ;
                    $('#counter-images').html(counter_images)
                    // </P>
                }
            })
            .fail(() => {
                this.errorMessage();
            })
            .always(function () {
                App.hide_loader();
            });
    }

    deleteProductImage(obj) {
        let imageId = obj.getAttribute('attr-image-id');
        let productId = $('#attr-product-id').attr('value');
        App.show_loader("#other-images-wrapper");
        $.ajax({
            method: "GET",
            url: window.reverse('builder:interactive_flyer_product_image_delete_api', [this.flyer_id, productId, imageId])
        })
            .done((data) => {
                if (data.status === 'deleted') {
                    $(`#oth-img-${imageId}`).remove();
                    // <P>
                    if($(`#${imageId}-img`).hasClass( "active" ) === true){
                        $('.carousel-control-next-icon.bg-primary').click()
                    }
                    setTimeout(function(){$(`#${imageId}-img`).remove();},1000)
                    var counter_images=$('#counter-images').text();
                    counter_images= counter_images - 1 ;
                    $('#counter-images').html(counter_images);
                    // </P>
                    if(counter_images == 1 ){
                        $('.carousel-control-prev').css('display','none');
                        $('.carousel-control-next').css('display','none');
                    }
                }
            })
            .fail(() => {
                this.errorMessage();
            })
            .always(function () {
                App.hide_loader("#other-images-wrapper");
            });
    }
    // endregion

    // region product interactivities
    saveProductInteraction(interaction){
        const modalId = `#${interaction}-interactivity-modal`;
        let productId = $('#attr-product-id').attr('value');
        let uploadImage = true;
        $(modalId).modal('hide');
        App.show_loader();
        const formData = new FormData();
        formData.append('title', $(`#edit-${interaction}-interactivity_title`).val());
        if ($(`#edit-${interaction}-interactivity_active`).is(':checked')) {
            formData.append('active', 'true');
        }
        var error_inter = 0

        switch(interaction) {
            case "world":
                if($('#edit-world-interactivity_active').is(':checked') && $('#edit-world-interactivity_link').val() == ''){
                    this.errorMessage(`${gettext('Inserisci un Link per attivare l\'interattività')}`)
                    error_inter=1
                    break;
                }
                formData.append('link', $(`#edit-${interaction}-interactivity_link`).val());
                uploadImage = false;
                break;

            case "play":
                const videoLink = $(`#edit-${interaction}-interactivity_link`).val();
                if(!videoLink  && !$(`#edit-${interaction}-interactivity_video_file`).val() && $(`#edit-play-interactivity_active`).is(':checked')){
                    App.hide_loader();
                    this.errorMessage(`${gettext('Inserisci un video per attivare l\'interattività')}`);
                    error_inter=1;
                    break;
                }
                if ($(`#edit-${interaction}-interactivity_show_icon`).is(':checked')) {
                    formData.append('show_icon', 'true');
                }
                if (videoLink != '') {
                    try {
                        let myRegexp = new RegExp("^.*(youtu.be\\/|v\\/|embed\\/|watch\\?|watch\\/|youtube.com\\/user\\/[^#]*#([^\\/]*?\\/)*)\\??v?=?([^#\\&\\?]*).*", "g");
                        let match = myRegexp.exec(videoLink);
                        formData.append('link', match[3]);
                    } catch (e) {
                        App.hide_loader();
                        this.errorMessage(`${gettext('Il link che hai inserito non è valido')}`);
                        return;
                    }
                } else{
                   let videoElement = $(`#edit-${interaction}-interactivity_video_file`);
                    if (videoElement[0].files) {
                        let videoFileData = videoElement[0].files[0];
                        formData.append("video_file", videoFileData);
                    }
                }
                
                uploadImage = false;
                $('#edit-play-interactivity_active').prop('checked',false);
                $('#edit-play-interactivity_video_preview').html('');
                break;

            case "hat-chef":
                if($(`#edit-${interaction}-interactivity_active`).is(':checked') && $('#edit-hat-chef-interactivity_ingredients').val() != '' && $('#edit-hat-chef-interactivity_recipe').val() != '') {
                    formData.append('ingredients', $(`#edit-${interaction}-interactivity_ingredients`).val());
                    formData.append('recipe', $(`#edit-${interaction}-interactivity_recipe`).val());
                } else if($(`#edit-${interaction}-interactivity_active`).is(':checked')) {
                    this.errorMessage(`${gettext('Inserisci sia gli ingredienti che la ricetta per attivare l\'interattività')}`);
                    error_inter = 1;
                }
                
                // image_file
                break;

            case "info":
                if($(`#edit-${interaction}-interactivity_active`).is(':checked') && $('#edit-info-interactivity_content-text').val() != '') {
                    formData.append('content_title', $(`#edit-${interaction}-interactivity_content-title`).val());
                    formData.append('content_text', $(`#edit-${interaction}-interactivity_content-text`).val());
                } else if($(`#edit-${interaction}-interactivity_active`).is(':checked')) {
                    this.errorMessage(`${gettext('Inserisci l\'informazione per attivare l\'interattività')}`);
                    error_inter = 1;
                }
                
                // image_file
                break;

            case "specs":
                if($(`#edit-${interaction}-interactivity_active`).is(':checked') && $(`#edit-${interaction}-interactivity_content-text`).val() != '') {
                    formData.append('content_text', $(`#edit-${interaction}-interactivity_content-text`).val());
                } else if($(`#edit-${interaction}-interactivity_active`).is(':checked')) {
                    this.errorMessage(`${gettext('Inserisci le specifiche per attivare l\'interattività')}`);
                    error_inter = 1;
                }
                
                // image_file
                break;

        }

        if(error_inter == 0) {
            if (uploadImage) {
                let imageElement = $(`#edit-${interaction}-interactivity_image_file`);
                if (imageElement[0].files) {
                    var imageFileData = imageElement[0].files[0];
                    formData.append("image_file", imageFileData);
                }
            }
            $(`#edit-${interaction}-interactivity_active`).attr('checked', 'false');

            $.ajax({
                method: "POST",
                url:  '/it' + window.reverse('builder:interactive_flyer_product_interactivity_api', [this.flyer_id, productId, interaction]),
                contentType: false,
                processData: false,
                data: formData,
            })
                .done((data) => {
                    const productIdx = this.searchProductIndex(productId, 'id');
                    if (data.status === 'ok') {
                        let markerIdx = -1;
                        $.each(this.productInPages[this.page_selected - 1][productIdx].markers,
                            (index, marker) => {
                                if (marker.type === interaction) {
                                    markerIdx = index;
                                }
                            });

                        if (markerIdx >= 0 && data.marker.active) {
                            // interattività aggiornata
                            this.productInPages[this.page_selected - 1][productIdx].markers[markerIdx] = data.marker;
                        } else if (markerIdx < 0 && data.marker.active) {
                            // interattività aggiunta
                            this.productInPages[this.page_selected - 1][productIdx].markers.push(data.marker);
                        } else if (markerIdx >= 0 && !data.marker.active) {
                            // interattività rimossa
                            this.productInPages[this.page_selected - 1][productIdx].markers.splice(markerIdx, 1);
                        }
                        this.reactor.dispatchEvent('limit_interactivity_product', this.productInPages[this.page_selected - 1][productIdx].markers);
                        this.showProductInteractionInPage(this.productInPages[this.page_selected - 1][productIdx].markers);
                    }
                })
                .fail(() => {
                    this.errorMessage();
                })
                .always(function () {
                    App.hide_loader();
                });
        }else{
            App.hide_loader();
            const productIdx = this.searchProductIndex(productId, 'id');
            this.reactor.dispatchEvent('limit_interactivity_product', this.productInPages[this.page_selected - 1][productIdx].markers);
            this.showProductInteractionInPage(this.productInPages[this.page_selected - 1][productIdx].markers);
        }
        
    }

    productInteractionModal(interaction) {
        // Pulisco gli input delle interattività

        // Video
        $('#edit-play-interactivity_active').prop('checked', false);
        $('#edit-play-interactivity_show_icon').prop('checked', false);
        $('#edit-play-interactivity_title').val('');
        $('#edit-play-interactivity_link').val('');
        $('#vf_radio').prop('checked', false);
        $('#yt_radio').prop('checked', false);
        $('#interaction-video_vf').addClass('d-none');
        $('#interaction-video_yt').addClass('d-none');
        $('label[for="edit-play-interactivity_video_file"]').html('');

        // Link
        $('#edit-world-interactivity_active').prop('checked', false);
        $('#edit-world-interactivity_title').val('');
        $('#edit-world-interactivity_link').val('');

        // Ricetta
        $(`#edit-hat-chef-interactivity_active`).prop('checked', false);
        $(`#edit-hat-chef-interactivity_title`).val('');
        $(`#edit-hat-chef-interactivity_ingredients`).val('');
        $(`#edit-hat-chef-interactivity_recipe`).val('');
        $(`#edit-hat-chef-interactivity_img`).removeClass('d-none');
        $(`#edit-hat-chef-interactivity_img img`).attr('src', '');
        $(`#edit-hat-chef-interactivity_img_preview`).html('');

        //Info
        $(`#edit-info-interactivity_active`).prop('checked', false);
        $(`#edit-info-interactivity_title`).val('');
        $(`#edit-info-interactivity_content-title`).val('');
        $(`#edit-info-interactivity_content-text`).val('');
        $(`#edit-info-interactivity_img`).addClass('d-none');
        $(`#edit-info-interactivity_img img`).attr('src', '');
        $(`#edit-info-interactivity_img_preview`).html('');
        $(`label[for="edit-info-interactivity_image_file"]`).text('Scegli immagine');

        //specifiche
        $(`#edit-specs-interactivity_active`).prop('checked', false);
        $(`#edit-specs-interactivity_title`).val('');
        $(`#edit-specs-interactivity_content-text`).val('');
        $(`#edit-specs-interactivity_img`).addClass('d-none');
        $(`#edit-specs-interactivity_img img`).attr('src', '');
        $(`#edit-specs-interactivity_img_preview`).html('');
        $(`label[for="edit-specs-interactivity_image_file"]`).text('Scegli immagine');

        const modalId = `#${interaction}-interactivity-modal`;
        let productId = $('#attr-product-id').attr('value');
        const product = this.productInPages[this.page_selected - 1][this.searchProductIndex(productId, 'id')];
        switch(interaction) {

            case "world":
                $(modalId).modal('show');
                product.markers.forEach((item) => {
                    if (item.type === interaction) {
                        $(`#edit-${interaction}-interactivity_active`).prop('checked', item.active);
                        $(`#edit-${interaction}-interactivity_title`).val(item.title);
                        $(`#edit-${interaction}-interactivity_link`).val(item.data);
                        $(modalId).on('hidden.bs.modal', function (e) {
                            $(`#edit-${interaction}-interactivity_active`).attr('checked', 'false');
                        });
                    }
                });
                break;

            case "play":
                $(modalId).modal('show');
                product.markers.forEach((item) => {
                    if (item.type === interaction) {
                        $(`#edit-${interaction}-interactivity_active`).prop('checked', item.active);
                        $(`#edit-${interaction}-interactivity_show_icon`).prop('checked', item.data.show_icon);
                        $('#edit-play-interactivity_show_icon').prop('checked',item.data.show_icon);
                        $(`#edit-${interaction}-interactivity_title`).val(item.title);
                        if (item.data.video_type === 'youtube') {
                            $('#yt_radio').prop('checked', true);
                            $('#interaction-video_vf').addClass('d-none');
                            $('#interaction-video_yt').removeClass('d-none');
                            $(`#edit-${interaction}-interactivity_video_yt`).removeClass('d-none');
                            $(`#edit-${interaction}-interactivity_video_yt iframe`).attr('src', "https://www.youtube.com/embed/" + item.data.link);
                            $(`#edit-${interaction}-interactivity_link`).val("https://www.youtube.com/watch/" + item.data.link);
                        } else if (item.data.video_type === 'video_file') {
                            $('#vf_radio').prop('checked', true);
                            $('#interaction-video_yt').addClass('d-none');
                            $('#interaction-video_vf').removeClass('d-none');
                            $(`#edit-${interaction}-interactivity_video`).removeClass('d-none');
                            $(`#edit-${interaction}-interactivity_video_yt`).addClass('d-none');
                            $(`#edit-${interaction}-interactivity_video_yt iframe`).attr('src', "");
                            $(`#edit-${interaction}-interactivity_video video`).attr('src', item.data.link);
                        }
                        $(modalId).on('hidden.bs.modal', function (e) {
                            // $(`#edit-${interaction}-interactivity_active`).attr('checked', 'false');
                            // $(`#edit-${interaction}-interactivity_show_icon`).attr('checked', 'false');
                            $(`#edit-${interaction}-interactivity_video`).addClass('d-none');
                            $(`#edit-${interaction}-interactivity_video_yt`).addClass('d-none');
                        });
                    }
                });
                break;

            case "hat-chef":
                $(modalId).modal('show');
                product.markers.forEach((item) => {
                    if (item.type === interaction) {
                        $(`#edit-${interaction}-interactivity_active`).prop('checked', item.active);
                        $(`#edit-${interaction}-interactivity_title`).val(item.title);
                        $(`#edit-${interaction}-interactivity_ingredients`).val(item.data.ingredients);
                        $(`#edit-${interaction}-interactivity_recipe`).val(item.data.recipe);
                        $(`#edit-${interaction}-interactivity_img`).removeClass('d-none');
                        $(`#edit-${interaction}-interactivity_img img`).attr('src', item.data.img[0]);
                        $(modalId).on('hidden.bs.modal', function (e) {
                            $(`#edit-${interaction}-interactivity_active`).attr('checked', item.active);
                            $(`#edit-${interaction}-interactivity_img`).addClass('d-none');
                        });
                    }
                });
                break;

            case "info":
                $(modalId).modal('show');
                product.markers.forEach((item) => {
                    if (item.type === interaction) {
                        $(`#edit-${interaction}-interactivity_active`).prop('checked', item.active);
                        $(`#edit-${interaction}-interactivity_title`).val(item.title);
                        $(`#edit-${interaction}-interactivity_content-title`).val(item.data.titolo);
                        $(`#edit-${interaction}-interactivity_content-text`).val(item.data.testo);
                        $(`#edit-${interaction}-interactivity_img`).removeClass('d-none');
                        $(`#edit-${interaction}-interactivity_img img`).attr('src', item.data.img[0]);
                    }
                    $(modalId).on('hidden.bs.modal', function (e) {
                        $(`#edit-${interaction}-interactivity_active`).prop('checked', false);
                        $(`#edit-${interaction}-interactivity_img`).addClass('d-none');
                    });
                });
                break;

            case "specs":
                $(modalId).modal('show');
                product.markers.forEach((item) => {
                    if (item.type === interaction) {
                        $(`#edit-${interaction}-interactivity_active`).prop('checked', item.active);
                        $(`#edit-${interaction}-interactivity_title`).val(item.title);
                        $(`#edit-${interaction}-interactivity_content-text`).val(item.data.specifiche);
                        $(`#edit-${interaction}-interactivity_img`).removeClass('d-none');
                        $(`#edit-${interaction}-interactivity_img img`).attr('src', item.data.img[0]);
                        $(modalId).on('hidden.bs.modal', function (e) {
                            $(`#edit-${interaction}-interactivity_active`).prop('checked', false);
                            $(`#edit-${interaction}-interactivity_img`).addClass('d-none');
                        });
                    }
                });
                break;

        }
    }

    showProductInteractionInPage(markers) {
        const interactionType = ["world", "play", "hat-chef", "info", "specs"];
        interactionType.forEach((aType) => {
            $(`#marker-${aType}-inactive`).removeClass('d-none');
            $(`#marker-${aType}-active`).addClass('d-none');
        });
        markers.forEach((item) => {
            $(`#marker-${item.type}-active`).removeClass('d-none');

            $(`#marker-${item.type}-inactive`).addClass('d-none');
        });

    }
    // endregion

    // region indice
    addIndexModal() {
        $('#add-index-modal').modal('show');
    }

    openModalUploadIndex() {
        $('#add-index-modal').modal('hide');
        $('#upload-index-modal').modal('show');
    }

    addExternalLinkIndexInteraction() {
        this.hideAllCards();
        setTimeout(() => {
            $("#add-external-link-index-card").fadeIn("slow");
            this.initImageCropper(true);
        }, 350);
        this.switchPanel('image');
    }

    addInternalLinkIndexInteraction() {
        this.hideAllCards();
        this.populatePageNumberSelect('#i-internal-link-index_page');
        setTimeout(() => {
            $("#add-internal-link-index-card").fadeIn("slow");
            this.initImageCropper(true);
        }, 350);
        this.switchPanel('image');
    }

    saveInternalLinkIndex() {
        let urlToSubmit = '/it' + window.reverse('builder:interactive_flyer_create_index_link_api', this.flyer_id);
        const formData = new FormData();
        const formParams = $('#i-internal-link-index-form').serializeArray();
        $.each(formParams, (i, val) => {
            if (val.name === 'id') {
                if (val.value !== '') {
                    formData.append(val.name, val.value);
                    urlToSubmit = '/it' + window.reverse('builder:interactive_flyer_edit_index_link_api', [this.flyer_id, val.value]);
                }
            } else {
                formData.append(val.name, val.value);
            }
        });

        App.show_loader();
        $.ajax({
            method: "POST",
            url: urlToSubmit,
            data: formData,
            contentType: false,
            processData: false,
        })
            .done((data) => {
                if (data.status === "created" ) {
                    this.pages.index.links.push(data.index);
                }
                if (data.status === "updated" ) {
                    let linkIndex = this.searchLinkIndexIndex(formData.get('id'));
                    this.pages.index.links.splice(linkIndex, 1);
                    this.pages.index.links.push(data.index);
                }
                this.undoInteractivity('internal_link_index');
                this.goToPage(-1);
            })
            .fail(() => {
                this.errorMessage();
            })
            .always(function () {
                App.hide_loader();
            });
    }

    saveExternalLinkIndex() {
        let urlToSubmit = '/it' + window.reverse('builder:interactive_flyer_create_index_link_api', this.flyer_id);
        const formData = new FormData();
        const formParams = $('#i-external-link-index-form').serializeArray();
        
        var validUrl= $('#i-external-link-index_url').val();
        if ( validUrl == ""){
            this.errorMessage(`${gettext('Aggiungi un url')}`);
            return
        }
        if(!(validUrl.includes('https://'))){
            validUrl='https://'+validUrl;
        }
        // var url = $('#i-external-link-index_url').val();
        // var url_validate = /(ftp|http|https):\/\/(\w+:{0,1}\w*@)?(\S+)(:[0-9]+)?(\/|\/([\w#!:.?+=&%@!\-\/]))?/;
        // if(!url_validate.test(url)){
        //     this.errorMessage(`${gettext('Inserisci un url valido')}`);
        //     return
        // }
        $.each(formParams, (i, val) => {
            if (val.name === 'id') {
                if (val.value !== '') {
                    formData.append(val.name, val.value);
                    urlToSubmit = '/it' + window.reverse('builder:interactive_flyer_edit_index_link_api', [this.flyer_id, val.value]);
                }
            } else {
                formData.append(val.name, val.value);
            }
        });
        formData.set('url',validUrl)
        App.show_loader();
        $.ajax({
            method: "POST",
            url: urlToSubmit,
            data: formData,
            contentType: false,
            processData: false,
        })
            .done((data) => {
                if (data.status === "created" ) {
                    this.pages.index.links.push(data.index);
                }
                if (data.status === "updated" ) {
                    let linkIndex = this.searchLinkIndexIndex(formData.get('id'));
                    this.pages.index.links.splice(linkIndex, 1);
                    this.pages.index.links.push(data.index);
                }
                this.undoInteractivity('external_link_index');
                this.goToPage(-1);
            })
            .fail(() => {
                this.errorMessage();
            })
            .always(function () {
                App.hide_loader();
            });
    }

    setLinkIndexInForm(link) {
        this.hideAllCards();
        if(link.type === 'url'){
            $('#i-external-link-index_id').val(link.id);
            $('#i-external-link-index_url').val(link.url);
            $('#i-external-link-index_title').val(link.title);
            $('#i-external-link-div-index_color').val(link.color);
            $('#i-external-link-style-index_color').css('background-color',link.color);
            setTimeout(() => {
                $("#add-external-link-index-card").fadeIn("slow");
                this.initImageCropper(false, link);
            }, 350);
        } else if (link.type === 'internal_link') {
            $('#i-internal-link-index_id').val(link.id);
            this.populatePageNumberSelect('#i-internal-link-index_page');
            $(`#i-internal-link-index_page option[value="${link.page}"]`).prop('selected', true);
            $(`#i-internal-link-index_title`).val(link.title);
            $(`#i-internal-link-div-index_color`).val(link.color);
            
            setTimeout(() => {
                $("#add-internal-link-index-card").fadeIn("slow");
                this.initImageCropper(false, link);
            }, 350);
        }
        this.switchPanel('image');
    }

    editIndexLink(obj){
        let linkId = obj.getAttribute('attr-link-id');
        let linkIndex = this.searchLinkIndexIndex(linkId);
        this.setLinkIndexInForm(this.pages.index.links[linkIndex]);
    }

    searchLinkIndexIndex(linkId) {
        let linkIndex = -1;
        for (let i = 0; i < this.pages.index.links.length; i++) {
            const lId = this.pages.index.links[i]['id'] + '';
            if (lId === linkId) {
                linkIndex = i;
            }
        }
        return linkIndex;
    }

    deleteIndexLink(obj) {
        App.show_loader();
        let linkId = obj.getAttribute('attr-link-id');
        $.ajax({
            method: "GET",
            url:  window.reverse('builder:interactive_flyer_delete_index_link_api', [this.flyer_id, linkId]),
        })
            .done((data) => {
                if (data.status === 'deleted') {
                    let linkIndex = this.searchLinkIndexIndex(linkId);
                    if (linkIndex >= 0) {
                        this.pages.index.links.splice(linkIndex, 1);
                        this.goToPage(-1);
                    }
                    if(linkIndex == 0){
                        $('tr.odd').hide();
                        $('tr.even').hide();
                    }
                    
                }
            })
            .fail(() => {
                this.errorMessage();
            })
            .always(function () {
                App.hide_loader();
            });
    }

    deleteFlyerIndex() {
        App.show_loader();
        $.ajax({
            method: "GET",
            url:  window.reverse('builder:interactive_flyer_delete_index_api', this.flyer_id),
        })
            .done((data) => {
                if (data.status === 'deleted') {
                    this.pages.index.page_url = '';
                    this.pages.index.links = [];
                    this.initPageBar();
                    this.page_selected = 1;
                    this.changePage();
                    $('#add-index-modal h5').html(`${gettext('Aggiungi indice')}`);
                }
            })
            .fail(() => {
                this.errorMessage();
            })
            .always(function () {
                App.hide_loader();
            });
    }

    indexManagement() {
        this.hideAllCards();
        const pageUrl = this.pages.index.page_url;
        $("#flyer-page-image").attr("src", pageUrl);
        $("#draw image").attr("src", pageUrl).attr("xlink:href", pageUrl);
        this.boxes.html('');
        var type=""
        
        $.each(this.pages.index.links, (_, value) => {
            if(value.type == 'plus'){
                type='product'
            }else if(value.type == 'play'){
                type='video'
            }
            else if(value.type == 'external-link' || value.type == 'internal_link' || value.type == 'url'){
                type='link'
            }
            this.drawRect(value.blueprint, value.id, type);
        });
        this.cardIndex();
        this.destroyImageCropper();

    }

    cardIndex() {
        setTimeout(() => {
            $("#index-card").fadeIn("slow");
            if (this.pages.index.links.length > 0) {
                $('#index-links-table').removeClass('d-none');
                let dtable = this.reInitDataTable('#index-links-table');
                dtable.DataTable({
                    language: {
                        url: '/static/gull-admin/js/plugins/localization/italian.json'
                    },
                    searching: false,
                    paging: false,
                    data: this.pages.index.links,
                    order: [[ 1, "desc" ]],
                    columns: [
                        {data: 'id', "visible": false},
                        {data: null,
                        render: function(data, type, row){
                                var tipo='';
                                if(data.type == 'internal_link'){
                                    tipo = 'Interno'
                                }else{
                                    tipo = 'Url'
                                }
                                return tipo
                        }
                        },
                        {data: null,
                            render: function(data, type, row){
                                    return data.title
                            }
                        },
                        {
                            data: null,
                            render: function (data, type, row) {
                                switch (row.type) {
                                    case 'url':
                                        return row.url;
                                    case 'internal_link':
                                        return row.page;
                                }
                            }
                        },
                        {data: null,
                            render: function(data, type, row){
                                    return data.color
                            }
                        },
                        {
                            data: null,
                            render: function (data, type, row) {
                                return `<button class="btn btn-secondary btn-sm" attr-link-id="${row.id}"
                                            onclick="editInteractiveFlyer.editIndexLink(this);"
                                            title="Modifica">
                                            <i _ngcontent-dkh-c8="" class="text-15 i-Pen-5"></i>
                                            </button>
                                        <button class="btn btn-danger btn-sm button-delete" attr-link-id="${row.id}"
                                            onclick="deleteElement(this,'link indice');"
                                            title="Cancella">
                                            <svg class="svg-delete" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 448 512"><defs><style>.cls-1{fill:#fff;}</style></defs><g id="Livello_2" data-name="Livello 2"><g id="Livello_1-2" data-name="Livello 1"><path class="cls-1" d="M432,32H312l-9.4-18.7A24,24,0,0,0,281.1,0H166.8a23.72,23.72,0,0,0-21.4,13.3L136,32H16A16,16,0,0,0,0,48V80A16,16,0,0,0,16,96H432a16,16,0,0,0,16-16V48A16,16,0,0,0,432,32ZM53.2,467a48,48,0,0,0,47.9,45H346.9a48,48,0,0,0,47.9-45L416,128H32Z"/></g></g></svg>
                                            </button>`;
                            }
                        }
                    ]
                });
            }
            App.hide_loader();
        }, 300);
    }
    // endregion

    // region price
    getPriceLabels() {
        $.ajax({
            method: "GET",
            url:  window.reverse('builder:get_price_labels_api', this.flyer_id),
        })
            .done((data) => {
                this.priceLabels = data;
                this.initPriceSelect();
            })
            .fail(() => {
                this.errorMessage();
            });
    }

    initPriceSelect() {
        const priceSelect = $("#i-product_calcolo_prezzo");
        priceSelect.change(() => {
            setTimeout(() => {
                const formProduct = $('#i-product-form');
                let force = true;
                if (formProduct.attr('new-product') === 'false') {
                    formProduct.removeAttr('new-product');
                    force = false;
                }
                let priceId = priceSelect.val();
                const groceryLabelElement = $('#i-product_grocery_label');
                const priceLabelElement = $('#i-product_price_label');
                const priceElement = $('#i-product_price_with_iva');
                const equivalenceElement = $('#i-product_equivalence');
                const quantityStepElement = $('#i-product_quantity_step');

                switch (priceId) {
                    case "1":
                        this.setElementIfEmpty(groceryLabelElement, this.priceLabels.piece_label, force);
                        this.setElementIfEmpty(priceLabelElement, `€ ${priceElement.val()}`, force);
                        this.setElementIfEmpty(equivalenceElement, '1', force);
                        this.setElementIfEmpty(quantityStepElement, '1', force);
                        break;
                    case "2":
                        this.setElementIfEmpty(groceryLabelElement, this.priceLabels.kg_label, force);
                        this.setElementIfEmpty(priceLabelElement, `€ ${priceElement.val()} ${this.priceLabels.kg_price_label}`, force);
                        this.setElementIfEmpty(equivalenceElement, '1', force);
                        this.setElementIfEmpty(quantityStepElement, '1', force);
                        break;
                    case "3":
                        this.setElementIfEmpty(groceryLabelElement, this.priceLabels.hectogram_label, force);
                        this.setElementIfEmpty(priceLabelElement, `€ ${priceElement.val()} ${this.priceLabels.kg_price_label}`, force);
                        this.setElementIfEmpty(equivalenceElement, '10', force);
                        this.setElementIfEmpty(quantityStepElement, '1', force);
                        break;
                    case "4":
                        this.setElementIfEmpty(groceryLabelElement, this.priceLabels.gr_label, force);
                        this.setElementIfEmpty(priceLabelElement, `€ ${priceElement.val()} ${this.priceLabels.kg_price_label}`, force);
                        this.setElementIfEmpty(equivalenceElement, '1000', force);
                        this.setElementIfEmpty(quantityStepElement, '100', force);
                        break;
                    case "5":
                        this.setElementIfEmpty(groceryLabelElement, this.priceLabels.hectogram_label, force);
                        this.setElementIfEmpty(priceLabelElement, `€ ${priceElement.val()} ${this.priceLabels.hectogram_price_label}`, force);
                        this.setElementIfEmpty(equivalenceElement, '1', force);
                        this.setElementIfEmpty(quantityStepElement, '1', force);
                        break;
                    case "6":
                        this.setElementIfEmpty(groceryLabelElement, this.priceLabels.gr_label, force);
                        this.setElementIfEmpty(priceLabelElement, `€ ${priceElement.val()} ${this.priceLabels.hectogram_price_label}`, force);
                        this.setElementIfEmpty(equivalenceElement, '10', force);
                        this.setElementIfEmpty(quantityStepElement, '1', force);
                        break;
                }
            }, 500);
        });
    }
    // endregion

    // region external link interaction
    addExternalLinkInteraction() {
        this.hideAllCards();
        setTimeout(() => {
            $('#i-external-link_show_tooltip').on('change', () => {
                this.showHideIfChecked($('#i-external-link_show_tooltip'), '#tooltip-external-link');
            });
            $("#add-external-link-card").fadeIn("slow");
            this.initImageCropper(true);
            this.switchPanel('image');
        }, 500);
    }

    editExternalLinkInteractionFromPage(obj) {
        let linkId = obj.getAttribute('attr-link-id');
        const externalLinkIdx = this.searchProductIndex(linkId, 'id');
        this.setExternalLinkInForm(this.productInPages[this.page_selected - 1][externalLinkIdx]);
    }

    setExternalLinkInForm(externalLink) {
        this.hideAllCards();
        $('#i-external-link_id').val(externalLink.id);

        let marker = {};
        externalLink.markers.forEach((aMarker) => {
           if (aMarker.type === 'external_link') {
               marker = aMarker;
           }
        });
        $(`#i-external-link-form input[value="${marker.data.link_type}"][name="link_type"]`).prop("checked", true);
        $(`#i-external-link_link_${marker.data.link_type}`).val(marker.data.link);
        $(`#i-external-link_link_${marker.data.link_type}_wrapper`).removeClass('d-none');
        if (marker.data.show_icon) {
            $('#i-external-link_show_icon').prop('checked', 'checked');
        }
        if (marker.data.tooltip !== '') {
            $('#i-external-link_show_tooltip').prop('checked', true);
            $('#i-external-link_tooltip').val(marker.data.tooltip);
            $('#tooltip-external-link').removeClass('d-none');
        }

        setTimeout(() => {
            $('#i-external-link_show_tooltip').on('change', () => {
                this.showHideIfChecked($('#i-external-link_show_tooltip'), '#tooltip-external-link');
            });
            $("#add-external-link-card").fadeIn("slow");
            this.initImageCropper(false, externalLink);
            this.switchPanel('image');
        }, 500);
    }

    linkTypeRadioClick(obj) {
        const radioValue = obj.getAttribute('value');
        switch (radioValue) {
            case 'url':
                $('#i-external-link_link_telephone_wrapper').addClass('d-none');
                $('#i-external-link_link_email_wrapper').addClass('d-none');
                $('#i-external-link_link_url_wrapper').removeClass('d-none');
                break;

            case 'email':
                $('#i-external-link_link_telephone_wrapper').addClass('d-none');
                $('#i-external-link_link_url_wrapper').addClass('d-none');
                $('#i-external-link_link_email_wrapper').removeClass('d-none');
                break;

            case 'telephone':
                $('#i-external-link_link_email_wrapper').addClass('d-none');
                $('#i-external-link_link_url_wrapper').addClass('d-none');
                $('#i-external-link_link_telephone_wrapper').removeClass('d-none');
                break;
        }
    }

    saveExternalLinkInteraction() {
        const interactionType = 'external_link';
        let urlToSubmit = '/it' + window.reverse('builder:interactive_flyer_interactivity_api', [this.flyer_id, interactionType]);
        const formData = new FormData();
        const formParams = $('#i-external-link-form').serializeArray();
        var url=false;
        $.each(formParams, (i, val) => {
            if (val.name === 'id') {
                if (val.value !== '') {
                    formData.append(val.name, val.value);
                    urlToSubmit = '/it' + window.reverse('builder:interactive_flyer_product_interactivity_api', [this.flyer_id, val.value, interactionType]);
                }
            } else {
                    formData.append(val.name, val.value);
            }
        });
        const linkTypeSelected = $('input[name=link_type]:checked', '#i-external-link-form').val();
        let interactionId = '';
        if (linkTypeSelected) {
            switch (linkTypeSelected) {
                case 'email':
                    const validEmail = $('#i-external-link_link_email').val();
                    if (validEmail === '') {
                        this.errorMessage(`${gettext('Inserisci un indirizzo email')}`);
                        return;
                    }
                    const reEmail = /^(([^<>()[\]\\.,;:\s@"]+(\.[^<>()[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
                    if (!reEmail.test(String(validEmail).toLowerCase())) {
                        this.errorMessage(`${gettext('Email non valida')}`);
                        return;
                    }
                    interactionId = '#i-external-link_link_email';
                    break;

                case 'url':
                    const validUrl = $('#i-external-link_link_url').val();
                    if (validUrl === '') {
                        this.errorMessage(`${gettext('Inserisci un url')}`);
                        return;
                    }
                    

                    // const reUrl = /^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)/;
                    // if (!reUrl.test(String(validUrl).toLowerCase())) {
                    //     this.errorMessage(`${gettext('Link non valido')}`);
                    //     return;
                    // }
                    interactionId = '#i-external-link_link_url';
                    break;

                case 'telephone':
                    const validTel = $('#i-external-link_link_telephone').val();
                    if (validTel === '') {
                        this.errorMessage(`${gettext('Inserisci un numero di telefono')}`);
                        return;
                    }
                    
                    const reTelephone = /^(\+{1})?(\d)*$/;
                    if (!reTelephone.test(String(validTel).toLowerCase())) {
                        this.errorMessage(`${gettext('Telefono non valido')}`);
                        return;
                    }
                    interactionId = '#i-external-link_link_telephone';
                    break;
            }
            formData.append('link', $(interactionId).val());
        } else {
            this.errorMessage(`${gettext('Seleziona una tipologia di link')}`);
            return;
        }
        formData.append('active', true);
        this.savePageInteraction(formData, interactionType, urlToSubmit);
    }
    // endregion

    // region internal link interaction
    addInternalLinkInteraction() {
        this.hideAllCards();
        setTimeout(() => {
            $('#i-internal-link_show_tooltip').on('change', () => {
                this.showHideIfChecked($('#i-internal-link_show_tooltip'), '#tooltip-internal-link');
            });
            this.populatePageNumberSelect('#i-internal-link_page_number');
            $("#add-internal-link-card").fadeIn("slow");
            this.initImageCropper(true);
            this.switchPanel('image');
        }, 500);
    }

    editInternalLinkInteractionFromPage(obj) {
        let linkId = obj.getAttribute('attr-link-id');
        const internalLinkIdx = this.searchProductIndex(linkId, 'id');
        this.setInternalLinkInForm(this.productInPages[this.page_selected - 1][internalLinkIdx]);
    }

    setInternalLinkInForm(internalLink) {
        this.hideAllCards();
        $('#i-internal-link_id').val(internalLink.id);

        let marker = {};
        internalLink.markers.forEach((aMarker) => {
           if (aMarker.type === 'internal_link') {
               marker = aMarker;
           }
        });
        if (marker.data.show_icon) {
            $('#i-internal-link_show_icon').prop('checked', 'checked');
        }
        if (marker.data.tooltip !== '') {
            $('#i-internal-link_show_tooltip').prop('checked', true);
            $('#i-internal-link_tooltip').val(marker.data.tooltip);
            $('#tooltip-internal-link').removeClass('d-none');
        }

        setTimeout(() => {
            $('#i-internal-link_show_tooltip').on('change', () => {
                this.showHideIfChecked($('#i-internal-link_show_tooltip'), '#tooltip-internal-link');
            });
            this.populatePageNumberSelect('#i-internal-link_page_number');
            $(`#i-internal-link_page_number option[value="${marker.data.page_number}"]`).prop('selected', true);
            $("#add-internal-link-card").fadeIn("slow");
            this.initImageCropper(false, internalLink);
            this.switchPanel('image');
        }, 500);
    }

    saveInternalLinkInteraction() {
        const interactionType = 'internal_link';
        let urlToSubmit = '/it' + window.reverse('builder:interactive_flyer_interactivity_api', [this.flyer_id, interactionType]);
        const formData = new FormData();
        const formParams = $('#i-internal-link-form').serializeArray();
        $.each(formParams, (i, val) => {
            if (val.name === 'id') {
                if (val.value !== '') {
                    formData.append(val.name, val.value);
                    urlToSubmit = '/it' + window.reverse('builder:interactive_flyer_product_interactivity_api', [this.flyer_id, val.value, interactionType]);
                }
            } else {
                formData.append(val.name, val.value);
            }
        });
        formData.append('active', true);
        this.savePageInteraction(formData, interactionType, urlToSubmit);
    }
    // endregion
    savePageInteraction(formData, interactionType, urlToSubmit){
        App.show_loader();
        this.cropper_item.cropper("getCroppedCanvas").toBlob((blob) => {  
            formData.append('cropped_image', blob, "cropped_image.png");
            formData.append('page', this.page_selected);
            $.ajax({
                method: "POST",
                url: urlToSubmit,
                data: formData,
                contentType: false,
                processData: false,
            })
                .done((data) => {
                    if (data.status === "created") {
                        this.productInPages[this.page_selected - 1].push(data.product);
                    } else if (data.status === "ok") {
                        let interactivityIndex = this.searchProductIndex(formData.get('id'), 'id');
                        this.productInPages[this.page_selected - 1].splice(interactivityIndex, 1);
                        this.productInPages[this.page_selected - 1].push(data.product);
                    }
                    this.undoInteractivity(interactionType);
                    this.changePage();
                })
                .fail((data) => {
                    this.errorMessage();
                })
                .always(function () {
                    App.hide_loader();
                });
        });
    }
};