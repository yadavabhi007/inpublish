from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db import models
from django_json_widget.widgets import JSONEditorWidget

from builder.models import (
    InteractiveFlyerProductVariety,
    InteractiveFlyerProject,
    Affiliate,
    ProductImage,
    ProductBlueprint,
    InteractiveFlyerProduct,
    InteractiveFlyerPage,
    InteractiveFlyer,
    CustomUser,
    ProjectSetting,
    ClientSetting,
    ProductMarker,
    ProductMarkerImage,
    PolotnoToken,
    InteractiveFlyerIndex,
    AWSUploader,
    InteractiveFlyerIndexLink,
    IndexLinkBlueprint,
)


class InteractiveFlyerProjectInline(admin.TabularInline):
    model = InteractiveFlyerProject
    extra = 0


class ProjectSettingInline(admin.StackedInline):
    model = ProjectSetting
    extra = 0
    formfield_overrides = {
        models.JSONField: {"widget": JSONEditorWidget},
    }


class IndexInline(admin.TabularInline):
    model = InteractiveFlyerIndex
    extra = 0


@admin.register(InteractiveFlyerPage)
class InteractiveFlyerPageAdmin(admin.ModelAdmin):
    model = InteractiveFlyerPage
    list_display = [
        "number",
        "interactive_flyer",
        ]
    formfield_overrides = {
        models.JSONField: {"widget": JSONEditorWidget},
    }
    search_fields = ["number", "interactive_flyer__name"]


@admin.register(InteractiveFlyer)
class InteractiveFlyerAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "name",
        "user",
        "status",
        "created_at"
    ]
    inlines = (
        IndexInline,
        InteractiveFlyerProjectInline,
        ProjectSettingInline,
    )


class ProductMarkerInline(admin.StackedInline):
    model = ProductMarker
    extra = 0


class ProductBlueprintInline(admin.TabularInline):
    model = ProductBlueprint
    extra = 0


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0


class InteractiveFlyerProductVarietyInline(admin.TabularInline):
    model = InteractiveFlyerProductVariety
    extra = 0


@admin.register(InteractiveFlyerProduct)
class InteractiveFlyerProductAdmin(admin.ModelAdmin):
    list_display = [
        "codice_interno_insegna",
        "description",
        "product_uid",
        "type",
        "interactive_flyer",
    ]
    list_filter = ("interactive_flyer_page__interactive_flyer__name",)
    search_fields = (
        "product_uid",
        "codice_interno_insegna",
        "field1",
        "interactive_flyer__name",
    )
    formfield_overrides = {
        models.JSONField: {"widget": JSONEditorWidget},
    }

    model = InteractiveFlyerProduct
    inlines = (
        ProductBlueprintInline,
        ProductImageInline,
        InteractiveFlyerProductVarietyInline,
        ProductMarkerInline,
    )


@admin.register(Affiliate)
class AffiliateAdmin(admin.ModelAdmin):
    model = Affiliate


class ClientSettingInline(admin.StackedInline):
    model = ClientSetting
    extra = 0


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ["username", "first_name", "last_name", "permission_pack"]
    inlines = (ClientSettingInline,)
    fieldsets = UserAdmin.fieldsets + (
        (
            "extrafields",
            {
                "fields": (
                    "token",
                    "connector_type",
                    "client_code",
                )
            },
        ),
        (
            "permissions",
            {
                "fields": (
                    "contemporary_publications_number",
                    "permission_pack",
                    "adsense",
                    "hide_share_grocery_list",
                    "hide_share_product",
                    "hide_product_page",
                    "hide_category_filter",
                    "number_interactivity_product",
                    "interactive_index",
                    "publication_date",
                    "grocery_list_create",
                    "video_in_page",
                    "search_product",
                    "single_product_share",
                    "product_select",
                    "product_page",
                    "website_integration",
                    "custom_opengraph_image_meta",
                    "custom_domain",
                    "grocery_list_to_market_integration",
                    "product_archive",
                    "analytics",
                    "highlight_product_added_to_grocery_list",
                    "variants_and_tags",
                )
            },
        ),
    )


@admin.register(ProjectSetting)
class ProjectSettingAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.JSONField: {"widget": JSONEditorWidget},
    }


admin.site.register(AWSUploader)
admin.site.register(InteractiveFlyerProject)
admin.site.register(ProductMarkerImage)
admin.site.register(PolotnoToken)


class IndexLinkBlueprintInline(admin.TabularInline):
    model = IndexLinkBlueprint
    extra = 0


@admin.register(InteractiveFlyerIndexLink)
class InteractiveFlyerIndexLinkAdmin(admin.ModelAdmin):
    model = InteractiveFlyerIndexLink
    inlines = (IndexLinkBlueprintInline,)
