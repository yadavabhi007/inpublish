import os

from django.conf import settings
from rest_framework import serializers
from builder.models import (
    IndexLinkBlueprint,
    InteractiveFlyerIndexLink,
    InteractiveFlyerIndex,
    ProductMarker,
    ProductImage,
    ProductBlueprint,
    InteractiveFlyerProduct,
    InteractiveFlyerPage,
    InteractiveFlyer,
    ProjectSetting,
    Affiliate,
    CustomUser,
)
from src.pillow.src.PIL import ImageColor
from utils.custom_logger import log_critical


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ("image_file", "cropped", "pk")


class ProductBlueprintSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductBlueprint
        fields = (
            "top",
            "left",
            "width",
            "height",
        )


class ProductMarkerSerializer(serializers.ModelSerializer):
    data = serializers.SerializerMethodField()

    class Meta:
        model = ProductMarker
        fields = (
            "type",
            "active",
            "title",
            "data",
        )

    def get_data(self, obj):
        if obj.type == "plus":
            return ""

        elif obj.type == "world":
            return obj.link

        elif obj.type == "external_link":
            return {
                "link_type": obj.link_type,
                "link": obj.link,
                "show_icon": obj.show_icon,
                "tooltip": obj.tooltip,
                "title": obj.title,
                "color": obj.color,
            }

        elif obj.type == "play":
            data = {
                "video_type": obj.video_type,
                "open_modal": obj.open_modal,
            }

            if obj.video_type == "video_file":
                data["link"] = obj.video_file.url
            elif obj.video_type == "youtube":
                data["link"] = obj.link
            if obj.open_modal:
                data["show_icon"] = obj.show_icon
                data["tooltip"] = obj.tooltip if obj.tooltip else ""

            return data

        elif obj.type == "hat-chef":
            img = []
            if obj.images.count() > 0 and obj.images.all()[0].image_file:
                img.append(obj.images.first().image_file.url)
            return {
                "ingredients": obj.ingredients,
                "recipe": obj.recipe,
                "img": img,
            }

        elif obj.type == "info":
            img = []
            if obj.images.count() > 0 and obj.images.all()[0].image_file:
                img.append(obj.images.first().image_file.url)
            return {
                "titolo": obj.content_title,
                "testo": obj.content_text,
                "img": img,
            }

        elif obj.type == "specs":
            img = []
            if obj.images.count() > 0 and obj.images.all()[0].image_file:
                img.append(obj.images.first().image_file.url)
            return {"specifiche": obj.content_text, "img": img}

        elif obj.type == "internal_link":
            return {
                "page_number": obj.page_number,
                "show_icon": obj.show_icon,
                "tooltip": obj.tooltip,
                "title": obj.title,
                "color": obj.color,
            }


class InteractiveFlyerProductSerializer(serializers.ModelSerializer):
    # markers = ProductMarkerSerializer(many=True, required=True)
    markers = serializers.SerializerMethodField("_get_markers")
    blueprint = ProductBlueprintSerializer(many=False, required=False)
    images = ProductImageSerializer(many=True, required=False)
    price = serializers.DecimalField(
        source="price_with_iva", max_digits=10, decimal_places=2
    )
    points = serializers.CharField(source="punti")
    varieties = serializers.StringRelatedField(many=True)
    item_id = serializers.SerializerMethodField("_get_item_id")
    category = serializers.SerializerMethodField("_get_category")
    subcategory = serializers.SerializerMethodField("_get_subcategory")
    category_id = serializers.SerializerMethodField("_get_category_id")
    subcategory_id = serializers.SerializerMethodField("_get_subcategory_id")
    weight_unit_of_measure = serializers.CharField()
    related = serializers.SerializerMethodField("_get_related")
    price_label = serializers.SerializerMethodField("_get_price_label")
    description = serializers.SerializerMethodField("_get_description")
    skul = serializers.SerializerMethodField("_get_skul")

    def _get_related(self, obj, exclude=None):
        to_return = []
        if obj.related.count() > 0:
            for rel_product in obj.related.all():
                if exclude is None or rel_product.id != exclude:
                    to_return.append(str(rel_product.id))
        elif obj.principal_product is not None:
            to_return = self._get_related(obj.principal_product, obj.id)
            to_return.append(str(obj.principal_product.id))

        return to_return

    def _get_price_label(self, obj):
        return f"{str(obj.price_label).replace('.', ',')}"

    def _get_item_id(self, obj):
        return f"{obj.id}"

    def _get_skul(self, obj):
        return obj.product_uid

    def _get_markers(self, obj):
        serializer = ProductMarkerSerializer(
            obj.markers.filter(active=True), many=True
        )
        return serializer.data

    def _get_category(self, obj):
        return obj.category_name

    def _get_subcategory(self, obj):
        return obj.subcategory_name

    def _get_category_id(self, obj):
        return obj.category

    def _get_subcategory_id(self, obj):
        return obj.subcategory

    def _get_description(self, obj):
        return obj.description()

    class Meta:
        model = InteractiveFlyerProduct
        fields = (
            "id",
            "ean_code",
            "codice_interno_insegna",
            "field1",
            "field2",
            "field3",
            "field4",
            "descrizione_estesa",
            "description",
            "grammage",
            "offer_price",
            "type",
            "item_id",
            "calcolo_prezzo",
            "price",
            "price_label",
            "equivalence",
            "quantity_step",
            "grocery_label",
            "varieties",
            "price_for_kg",
            "available_pieces",
            "max_purchasable_pieces",
            "points",
            "fidelity_product",
            "focus",
            "pam",
            "three_for_two",
            "one_and_one_gratis",
            "underpriced_product",
            "category",
            "subcategory",
            "category_id",
            "subcategory_id",
            "blueprint",
            "images",
            "markers",
            "weight_unit_of_measure",
            "strike_price",
            "discount_rate",
            "prices",
            "promo",
            "stock",
            "tdc",
            "sku",
            "skul",
            "available_from",
            "related",
            "brand",
            "brand_logo",
            "line",
            "line_logo",
        )


class InteractiveFlyerPageSerializer(serializers.ModelSerializer):
    interactivities = serializers.SerializerMethodField("_get_interactivities")

    def _get_interactivities(self, obj):
        if obj.products.count() > 0:
            serialzier = InteractiveFlyerProductSerializer(
                obj.products.all(), many=True
            )
            return serialzier.data
        else:
            return []

    class Meta:
        model = InteractiveFlyerPage
        fields = (
            "number",
            "image_file",
            "thumb_image_file",
            "interactivities",
        )


class IndexLinkBlueprintSerializer(serializers.ModelSerializer):
    class Meta:
        model = IndexLinkBlueprint
        fields = (
            "top",
            "left",
            "width",
            "height",
        )


class InteractiveFlyerIndexLinkSerializer(serializers.ModelSerializer):
    blueprint = IndexLinkBlueprintSerializer(many=False, required=False)

    class Meta:
        model = InteractiveFlyerIndexLink
        fields = (
            "id",
            "page",
            "blueprint",
            "target",
            "title",
            "color",
            "url",
            "type",
        )


class InteractiveFlyerIndexSerializer(serializers.ModelSerializer):
    links = InteractiveFlyerIndexLinkSerializer(many=True, required=False)

    class Meta:
        model = InteractiveFlyerIndex
        fields = (
            "image_file",
            "thumb_image_file",
            "links",
        )


class InteractiveFlyerPortaleSerializer(serializers.ModelSerializer):
    publication_date = serializers.SerializerMethodField(
        "_get_publication_date"
    )
    expiration_date = serializers.SerializerMethodField("_get_expiration_date")
    first_page = serializers.SerializerMethodField("_get_first_page")

    def _get_publication_date(self, obj):
        return obj.settings.publicationDate

    def _get_expiration_date(self, obj):
        return obj.settings.expirationDate

    def _get_first_page(self, obj):
        return InteractiveFlyerPageSerializer(obj.pages.first()).data

    class Meta:
        model = InteractiveFlyer
        fields = (
            "id",
            "name",
            "first_page",
            "publication_date",
            "expiration_date",
            "status",
        )


class InteractiveFlyerSerializer(serializers.ModelSerializer):
    code = serializers.SerializerMethodField("_get_code")
    id_campaign = serializers.SerializerMethodField("_get_id_campaign")
    pages = serializers.SerializerMethodField("_get_pages")
    index = InteractiveFlyerIndexSerializer(many=False, required=False)

    def _get_code(self, obj):
        return f"{obj.pk}"

    def _get_pages(self, obj):
        all_pages = []
        for page in obj.pages.all().order_by("number"):
            all_pages.append(page.json_page)

        return all_pages

    def _get_id_campaign(self, obj):
        if obj.projects.count() == 0:
            return ""
        else:
            return f"{obj.projects.first().project_id}"  # TODO un solo progetto correlato

    class Meta:
        model = InteractiveFlyer
        fields = (
            "id",
            "code",
            "id_campaign",
            "name",
            "index",
            "categories",
            "pages",
            "status",
            "initialization_error_message",
            "initialization_error",
            "initialization_in_progress",
            "publication_url",
        )


class ProjectSettingSerializer(serializers.ModelSerializer):
    pdfPath = serializers.SerializerMethodField("_get_pdf_path")
    noIconAnimated = serializers.SerializerMethodField("_get_no_icon_animated")
    ogImageMeta_mobile = serializers.SerializerMethodField(
        "_get_og_image_meta_mobile"
    )
    serverPath = serializers.SerializerMethodField("_get_server_path")
    hover_color = serializers.SerializerMethodField("_get_hover_color")
    adsense = serializers.SerializerMethodField("_get_adsense")
    hide_share_grocery_list = serializers.SerializerMethodField(
        "_get_hide_share_grocery_list"
    )
    hide_share_product = serializers.SerializerMethodField(
        "_get_hide_share_product"
    )
    hide_product_page = serializers.SerializerMethodField(
        "_get_hide_product_page"
    )
    hide_category_filter = serializers.SerializerMethodField(
        "_get_hide_category_filter"
    )
    only_browsable = serializers.SerializerMethodField("_get_only_browsable")
    hide_grocery_list = serializers.SerializerMethodField(
        "_get_hide_grocery_list"
    )
    hide_searchbar = serializers.SerializerMethodField("_get_hide_searchbar")
    clientIcon = serializers.SerializerMethodField("_get_client_icon")
    client_code = serializers.SerializerMethodField("_get_client_code")
    slug = serializers.SerializerMethodField("_get_slug")
    flyer_status = serializers.SerializerMethodField("_get_flyer_status")
    release_id = serializers.SerializerMethodField("_get_release_id")
    ga_active = serializers.SerializerMethodField("_get_ga_active")

    def _get_ga_active(self, obj):
        return True

    def _get_release_id(self, obj):
        return f"{obj.release_id}"

    def _get_flyer_status(self, obj):
        return obj.interactive_flyer.status

    def _get_client_code(self, obj):
        return obj.interactive_flyer.user.client_code

    def _get_slug(self, obj):
        return obj.interactive_flyer.slug

    def _get_client_icon(self, obj):
        if obj.clientIcon:
            return obj.clientIcon.url
        else:
            return (
                f"{settings.ABSOLUTE_URL}/static/builder/img/interattivo.png"
            )

    def _get_adsense(self, obj):
        return obj.interactive_flyer.user.adsense

    def _get_hide_share_grocery_list(self, obj):
        return obj.interactive_flyer.user.hide_share_grocery_list

    def _get_hide_share_product(self, obj):
        return obj.interactive_flyer.user.hide_share_product

    def _get_hide_product_page(self, obj):
        return obj.interactive_flyer.user.hide_product_page

    def _get_hide_category_filter(self, obj):
        return obj.interactive_flyer.user.hide_category_filter

    def _get_hover_color(self, obj):
        rgb = ImageColor.getcolor(obj.hover_color, "RGB")
        return f"rgba({rgb[0]},{rgb[1]},{rgb[2]},0.5)"

    def _get_server_path(self, obj):
        # return os.getenv("https://view.interattivo.net/", "https://view.interattivo.net/")
        return "https://view.interattivo.net/"

    def _get_no_icon_animated(self, obj):
        return obj.iconAnimation == ""

    def _get_pdf_path(self, obj):
        return obj.interactive_flyer.flyer_pdf_file.url

    def _get_og_image_meta_mobile(self, obj):
        return obj.ogImageMeta_mobile.url if obj.ogImageMeta_mobile else ""

    def _get_only_browsable(self, obj):
        return (
            True
            if obj.interactive_flyer.user.permission_pack == CustomUser.FREE
            else obj.only_browsable
        )

    def _get_hide_searchbar(self, obj):
        return (
            True
            if obj.interactive_flyer.user.permission_pack == CustomUser.FREE
            else obj.hide_searchbar
        )

    def _get_hide_grocery_list(self, obj):
        return (
            True
            if obj.interactive_flyer.user.permission_pack == CustomUser.FREE
            else obj.hide_grocery_list
        )

    class Meta:
        model = ProjectSetting
        exclude = [
            "id",
            "interactive_flyer",
            "videoInPage",
            "publicationDate",
            "hectogram_price_label",
            "kg_price_label",
            "kg_label",
            "hectogram_label",
            "gr_label",
            "piece_label",
            "price_label",
        ]


class AffiliateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Affiliate
        fields = "__all__"
