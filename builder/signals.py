from django.conf import settings
from django.contrib.auth.signals import user_logged_in
from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.utils import timezone

from builder.models import (
    ProjectSetting,
    InteractiveFlyer,
    ProductMarker,
    ClientSetting,
    InteractiveFlyerProduct,
    InteractiveFlyerPage,
    ProductBlueprint,
    ProductImage,
)
from builder.serializers import InteractiveFlyerPageSerializer
from builder.utils.decorators import threaded
from utils.custom_logger import log_debug, log_critical


@receiver(post_save, sender=ProjectSetting)
@receiver(post_save, sender=InteractiveFlyer)
def update_flyer_status(sender, instance, **kwargs):
    if hasattr(instance, "_dirty"):
        return
    instance._dirty = True  # per evitare il loop

    if sender == ProjectSetting:
        instance = instance.interactive_flyer

    try:
        if (
            instance.settings.expirationDate
            and timezone.now() > instance.settings.expirationDate
        ):
            instance.status = InteractiveFlyer.EXPIRED
        elif (
            instance.settings.publicationDate
            and instance.settings.publicationDate != ""
            and instance.settings.publicationDate > timezone.now()
        ):
            instance.status = InteractiveFlyer.SCHEDULED
        elif (
            instance.settings.publicationDate is None
            or instance.settings.publicationDate == ""
        ) and instance.status == InteractiveFlyer.SCHEDULED:
            instance.status = InteractiveFlyer.DRAFT
        instance.save()
    except Exception:
        pass


@receiver(pre_save, sender=ProjectSetting)
def increment_version_project_settings_signal(sender, instance, **kwargs):
    if instance.ga_tracking_id == "":
        instance.ga_tracking_id = settings.INTERATTIVO_ANALYTICS
    if instance.expirationDate is None or instance.expirationDate == "":
        time_to_set = timezone.now().replace(year=2099)
        instance.expirationDate = time_to_set

    if len(instance.sidebar) == 0:
        instance.sidebar.append(instance.type)

    instance.version = instance.version + 1


@receiver(pre_save, sender=ProductMarker)
def check_external_url(sender, instance, **kwargs):
    if (
        instance.link
        and not instance.link.startswith("http://")
        and not instance.link.startswith("https://")
        and instance.type != "play"
        and instance.link_type != "telephone"
        and instance.link_type != "email"
    ):
        instance.link = f"https://{instance.link}"


@receiver(user_logged_in)
def user_logged_in_callback(sender, user, request, **kwargs):
    from builder.utils.base_class.permissions_class import PermissionsUtils

    try:
        pu = PermissionsUtils()
        permissions = pu.get_permissions(user)

        if (
            len(permissions["pacchetto"]) > 0
            and len(permissions["caratteristiche"]) > 0
        ):
            user.contemporary_publications_number = pu.search_perm_by_id(2, 1)
            user.adsense = not pu.search_perm_by_id(5, False)
            user.hide_share_grocery_list = not pu.search_perm_by_id(17, False)
            user.hide_share_product = not pu.search_perm_by_id(24, False)
            user.hide_product_page = not pu.search_perm_by_id(27, False)
            user.hide_category_filter = not pu.search_perm_by_id(28, False)

            user.number_interactivity_product = pu.search_perm_by_id(12, False)
            user.interactive_index = pu.search_perm_by_id(14, False)
            user.publication_date = pu.search_perm_by_id(15, False)
            user.grocery_list_create = pu.search_perm_by_id(16, False)
            user.video_in_page = pu.search_perm_by_id(19, False)
            user.search_product = pu.search_perm_by_id(23, False)
            user.single_product_share = pu.search_perm_by_id(24, False)
            user.product_select = pu.search_perm_by_id(26, False)
            user.product_page = pu.search_perm_by_id(27, False)
            user.website_integration = pu.search_perm_by_id(33, False)
            user.custom_opengraph_image_meta = pu.search_perm_by_id(35, False)
            user.custom_domain = pu.search_perm_by_id(36, False)
            user.grocery_list_to_market_integration = pu.search_perm_by_id(37, False)
            user.product_archive = pu.search_perm_by_id(43, False)
            user.analytics = True if pu.search_perm_by_id(60, False) > 0 else False
            user.highlight_product_added_to_grocery_list = pu.search_perm_by_id(123, False)
            user.variants_and_tags = pu.search_perm_by_id(124, False)

            user.permission_pack = permissions["pacchetto"]["id"]

            user.save()
    except Exception as e:
        log_debug("Exception!!!", f"{e}")


# TODO completa la cancellazione delle immagini (dopo la fiera)
# @receiver(pre_delete, sender=ProjectSetting)
# @receiver(pre_delete, sender=ClientSetting)
def clean_image_project_settings(sender, instance, **kwargs):
    if sender == ProjectSetting:
        user = instance.interactive_flyer.user
    else:
        user = instance.user_client

    user_flyers = user.flyers.all()
    log_debug(
        "clean_image_project_settings",
        f"ClientSetting: {sender == ClientSetting} - "
        f"ProjectSetting: {sender == ProjectSetting}",
    )

    files_to_check = [
        "clientIcon",
        "videoInPage",
        "brandImage",
        "underPriceImage",
    ]
    for file in files_to_check:
        to_delete = True
        for a_flyer in user_flyers:
            log_debug(
                "clean_image_project_settings -> volantino: ", a_flyer.name
            )
            try:
                log_debug(
                    "clean_image_project_settings",
                    f"{getattr(a_flyer.settings, file).size} == "
                    f"{getattr(instance, file).size}",
                )
                if (
                    getattr(a_flyer.settings, file).name
                    == getattr(instance, file).name
                    and getattr(a_flyer.settings, file).size
                    == getattr(instance, file).size
                ):
                    to_delete = False
            except Exception as e:
                to_delete = False

        log_debug("clean_image_project_settings", to_delete)
        if to_delete:
            if sender == ClientSetting:
                log_debug("clean_image_project_settings", to_delete)
                storage, path = (
                    getattr(instance, file).storage,
                    getattr(instance, file).path,
                )
                storage.delete(path)
            elif (
                getattr(user.settings, file).path
                != getattr(instance, file).path
            ):
                log_debug("clean_image_project_settings", to_delete)
                storage, path = (
                    getattr(instance, file).storage,
                    getattr(instance, file).path,
                )
                storage.delete(path)


@receiver(post_save, sender=InteractiveFlyerProduct)
@receiver(post_delete, sender=InteractiveFlyerProduct)
@receiver(post_save, sender=ProductMarker)
@receiver(post_save, sender=ProductBlueprint)
@receiver(post_save, sender=ProductImage)
@receiver(post_save, sender=InteractiveFlyerPage)
def generate_json_page(sender, instance, **kwargs):
    if hasattr(instance, "_dirty"):
        return
    page = None
    if sender == InteractiveFlyerProduct:
        page = instance.interactive_flyer_page
    elif (
        sender == ProductBlueprint
        or sender == ProductMarker
        or sender == ProductImage
    ):
        page = instance.interactive_flyer_product.interactive_flyer_page
    elif sender == InteractiveFlyerPage:
        page = instance

    page.json_page = InteractiveFlyerPageSerializer(page).data
    try:
        instance._dirty = True
        page.save()
    finally:
        del instance._dirty  # noqa

    # async_function(sender, instance)


# @threaded
# def async_function(sender, instance):
    