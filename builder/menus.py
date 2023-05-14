from django.urls import reverse, resolve
from django.utils.translation import ugettext_lazy as _
from menu import Menu, MenuItem

from builder.utils.interattivo_menu_item import InterattivoMenuItem

Menu.add_item(
    "main_menu",
    MenuItem(
        _("Dashboard"),
        reverse("builder:dashboard"),
        icon="i-Bar-Chart",
        svg='<img style="height:30px" src="/static/icons/Dashborad.svg">',
        weight=10,
        html_id="dashboard",
        check=lambda request: resolve(request.path_info).url_name
        != "edit_interactive_flyer",
    ),
)
Menu.add_item(
    "main_menu",
    MenuItem(
        _("Nuovo"),
        reverse("builder:new_interactive_flyer"),
        icon="i-Add-File",
        svg='<img style="height:30px" src="/static/icons/Nuovo.svg">',
        weight=10,
        html_id="dashboard",
        check=lambda request: resolve(request.path_info).url_name
        != "edit_interactive_flyer",
    ),
)

# region profile_menu
Menu.add_item(
    "profile_menu",
    MenuItem(
        _("Impostazioni cliente"),
        reverse("builder:setting_client"),
        weight=10,
    ),
)
Menu.add_item(
    "profile_menu",
    MenuItem(
        _("Database admin"),
        reverse("admin:index"),
        check=lambda request: request.user.is_superuser,
        weight=20,
    ),
)
Menu.add_item(
    "profile_menu",
    MenuItem(
        _("Esci"),
        reverse("builder:logout"),
        weight=100,
    ),
)
# endregion

# region editor menu
Menu.add_item(
    "main_menu",
    InterattivoMenuItem(
        _("Indice"),
        "#",
        function="editInteractiveFlyer.addIndexModal()",
        icon="i-Book",
        id_perms="perm-interactive_index",
        svg='<img style="height:30px" src="/static/icons/Index.svg">',
        weight=10,
    ),
)
Menu.add_item(
    "main_menu",
    InterattivoMenuItem(
        _("Prodotto"),
        "#",
        function="editInteractiveFlyer.addProductInteraction();",
        is_free=False,
        is_essential=True,
        icon="i-Cursor-Click-2",
        svg='<img style="height:30px" src="/static/icons/Product.svg">',
        id_perms="interactivity-product",
        weight=15,
    ),
)
Menu.add_item(
    "main_menu",
    InterattivoMenuItem(
        _("Video"),
        "#",
        function="editInteractiveFlyer.addVideoInteraction();",
        is_free=False,
        is_essential=True,
        icon="i-Film-Video",
        svg='<img style="height:30px" src="/static/icons/Video.svg">',
        id_perms="interactivity-video",
        weight=20,
    ),
)
Menu.add_item(
    "main_menu",
    InterattivoMenuItem(
        _("Link esterno"),
        "#",
        function="editInteractiveFlyer.addExternalLinkIndexInteraction();",
        is_free=True,
        is_essential=True,
        icon="i-URL-Window",
        svg='<img style="height:30px" src="/static/icons/External-link.svg">',
        id_perms="interactivity-index-external-link",
        nav_class="d-none",
        weight=25,
    ),
)
Menu.add_item(
    "main_menu",
    InterattivoMenuItem(
        _("Link esterno"),
        "#",
        function="editInteractiveFlyer.addExternalLinkInteraction();",
        is_free=False,
        is_essential=True,
        icon="i-URL-Window",
        id_perms="interactivity-product-external-link",
        svg='<img style="height:30px" src="/static/icons/External-link.svg">',
        weight=25,
    ),
)
Menu.add_item(
    "main_menu",
    InterattivoMenuItem(
        _("Link interno"),
        "#",
        function="editInteractiveFlyer.addInternalLinkInteraction();",
        is_free=False,
        is_essential=True,
        icon="i-File-Link",
        id_perms="interactivity-product-internal-link",
        svg='<img style="height:30px" src="/static/icons/Internal-link.svg">',
        weight=30,
    ),
)
Menu.add_item(
    "main_menu",
    InterattivoMenuItem(
        _("Link interno"),
        "#",
        function="editInteractiveFlyer.addInternalLinkIndexInteraction();",
        is_free=True,
        is_essential=True,
        icon="i-File-Link",
        id_perms="interactivity-index-internal-link",
        svg='<img style="height:30px" src="/static/icons/Internal-link.svg">',
        nav_class="d-none",
        weight=30,
    ),
)
# endregion
