/* jshint esversion: 6 */

let PermissionsManagerClass = class PermissionsManager {

    constructor() {
        if (PermissionsManager._instance) {
          return PermissionsManager._instance;
        }
        PermissionsManager._instance = this;
        // this.lsm = new LocalStorageManagerClass();
        this.permissions = {} 
        this.default_message = `${gettext('Funzionalità non attiva. Scopri i piani di InPublish!')}`;
        this.tooltip_params = {
            'data-toggle': 'tooltip',
            'data-placement': 'top',
            'title': this.default_message
        };

        this.interactionType = ["world", "play", "hat-chef", "info", "specs"];

        this.reactor = reactorSingleton.getInstance();
        this.reactor.registerEvent('limit_interactivity_product');
        this.reactor.registerEvent('release_interactivity_product');

        this.reactor.addEventListener('limit_interactivity_product', (markers) => {
            if ((markers.length - 1) >= this.permissions.number_interactivity_product ) {
                
                this.interactionType.forEach((aType) => {
                    let flag = true;
                    for (let idx = 0; idx < markers.length; idx++) {
                        if (markers[idx].type === aType) {
                            flag = false;
                        }
                    }
                    if (flag) {
                        $(`.product-button-interactivity.${aType}`).addClass('no-permission').attr(this.tooltip_params);
                        $(`.product-button-interactivity.${aType} button`).renameAttr('onclick', 'onclickd');
                    }
                });
            } else {
                this.reactor.dispatchEvent('release_interactivity_product');
            }
        });
        this.reactor.addEventListener('release_interactivity_product', () => {
            this.interactionType.forEach((aType) => {
                $(`.product-button-interactivity.${aType}`).removeClass('no-permission');
                let button = $(`.product-button-interactivity.${aType} button`);
                if (button.attr('onclickd')) {
                    button.renameAttr('onclickd', 'onclick');
                }
            });
        });
    }


    checkPermissions() {
            $.ajax(
                {
                    method: "GET",
                    url: window.reverse('builder:get_permissions_api')
                })
                .done((response) => {
                    if (response.success) {
                        this.permissions = response.perms
                        // for (const [key, value] of Object.entries(response.perms)) {
                            // this.lsm.set(key, value);
                        // }
                        // this.lsm.set('permissions', 'true');
                        // this.applyPermissions();
                    } else {
                        window.location.href = window.reverse('builder:error_page');
                    }
                })
                .fail(() => {
                    Swal.fire({
                        icon: 'error',
                        title: `${gettext('Oops...')}`,
                        text: `${gettext('Qualcosa è andato storto, aggiorna la pagina e riprova.')}`,
                    });
                });
    }

    applyPermissions() {
        let name;
        let element;

        // project settings
        name = 'single_product_share';  // Condivisione singolo prodotto
        element = $('#perm-' + name);
        if (element.length && !this.permission[name]) {
            // TODO
        }

        name = 'product_select';  // Prodotti correlati
        element = $('#perm-' + name);
        if (element.length && !this.permission[name]) {
            // TODO
        }

        name = 'website_integration';  // Integrazione in sito web
        element = $('#perm-' + name);
        if (element.length && !this.permission[name]) {
            $(element).addClass('no-permission').attr(this.tooltip_params);
        }

        name = 'product_archive';  // Archivio prodotti
        if (!this.permission[name]) {
            $('#perm-filterUnderprice').addClass('no-permission').attr(this.tooltip_params);
            $('#perm-interactivityIcon').addClass('no-permission').attr(this.tooltip_params);
            $('#perm-banners').addClass('no-permission').attr(this.tooltip_params);
            $('#perm-labels').addClass('no-permission').attr(this.tooltip_params);
        }

        name = 'variants_and_tags';  // Varianti e Tag
        element = $('#perm-' + name);
        if (element.length && !this.permission[name]) {
            $(element).addClass('no-permission').attr(this.tooltip_params);
            $('.perm-tags').addClass('no-permission').attr(this.tooltip_params);
        }

        if (this.permission['is_free_user']) {
            $('#interactivity-product').attr(this.tooltip_params);
            $('#interactivity-video').attr(this.tooltip_params);
            $('#interactivity-product-external-link').attr(this.tooltip_params);
            $('#interactivity-product-internal-link').attr(this.tooltip_params);
        }

        if (this.permission['is_essential_user']) {
            $('#interactivity-product').attr(this.tooltip_params);
        }

        setTimeout(() => {
            $.each($( ".no-permission input" ), (_, item) => {
                $(item).attr('disabled', 'disabled');
            });

            $.each($(".no-permission i, .no-permission a"), (_, item) => {
                $(item).attr('onclick', '');
            });
        }, 100);
    }
};