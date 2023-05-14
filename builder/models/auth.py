from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django_cleanup import cleanup
from rest_framework.authtoken.models import Token

from builder.utils.service import generate_token


class CustomUser(AbstractUser):
    token = models.CharField(
        max_length=100, default=generate_token, unique=True, db_index=True
    )
    client_code = models.CharField(
        max_length=100, unique=True, default=None, null=True, db_index=True
    )
    # region permission fields
    contemporary_publications_number = models.PositiveIntegerField(default=1)
    adsense = models.BooleanField(default=False)
    hide_share_grocery_list = models.BooleanField(default=False)
    hide_share_product = models.BooleanField(default=False)
    hide_product_page = models.BooleanField(default=False)
    hide_category_filter = models.BooleanField(default=False)

    number_interactivity_product = models.SmallIntegerField(default=1)  # 12
    interactive_index = models.BooleanField(default=False)  # 14
    publication_date = models.BooleanField(default=False)  # 15
    grocery_list_create = models.BooleanField(default=False)  # 16
    video_in_page = models.BooleanField(default=False)  # 19
    search_product = models.BooleanField(default=False)  # 23
    single_product_share = models.BooleanField(default=False)  # 24
    product_select = models.BooleanField(default=False)  # 26
    product_page = models.BooleanField(default=False)  # 27
    website_integration = models.BooleanField(default=False)  # 33
    custom_opengraph_image_meta = models.BooleanField(default=False)  # 35
    custom_domain = models.BooleanField(default=False)  # 36
    grocery_list_to_market_integration = models.BooleanField(default=False)  # 37
    product_archive = models.BooleanField(default=False)  # 43
    analytics = models.BooleanField(default=False)  # 60
    highlight_product_added_to_grocery_list = models.BooleanField(default=False)  # 123
    variants_and_tags = models.BooleanField(default=False)  # 124

    FREE = 1
    ESSENTIAL = 2
    STANDARD = 3
    PREMIUM = 4
    ENTERPRICE = 5
    PERMISSION_CHOICES = [
        (FREE, "free user"),
        (ESSENTIAL, "essential"),
        (STANDARD, "standard"),
        (PREMIUM, "premium"),
        (ENTERPRICE, "enterprice"),
    ]
    permission_pack = models.IntegerField(
        choices=PERMISSION_CHOICES, default=1
    )
    # endregion
    CONNECTOR_TYPE_CHOICES = [
        (settings.USER_TYPE_AEB, "AEB"),
        (settings.USER_TYPE_INTERNAL, "internal"),
        (settings.USER_TYPE_GIODICART, "giodicart"),
    ]
    connector_type = models.CharField(
        max_length=30, choices=CONNECTOR_TYPE_CHOICES, default="internal"
    )

    def is_free_user(self):
        return self.permission_pack == self.FREE

    def is_essential_user(self):
        return self.permission_pack == self.ESSENTIAL

    class Meta:
        permissions = [
            ("free_pack", "free_pack"),
            ("essential_pack", "essential_pack"),
            ("standard_pack", "standard_pack"),
            ("premium_pack", "premium_pack"),
            ("enterprice_pack", "enterprice_pack"),
        ]
        indexes = [
            models.Index(fields=['client_code','token']),
        ]


@cleanup.ignore
class ClientSetting(models.Model):
    user_client = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, related_name="settings"
    )
    # DATI CLIENTE
    client_id = models.IntegerField(
        default=0, unique=True, blank=False, null=True
    )
    signboard_id = models.IntegerField(default=0)
    release_id = models.IntegerField(default=0)
    # GRAFICA
    primary_color = models.CharField(
        default="#000000", blank=False, null=False, max_length=500
    )
    secondary_color = models.CharField(
        default="#000000", blank=False, null=False, max_length=500
    )
    tertiary_color = models.CharField(
        default="#000000", blank=False, null=False, max_length=500
    )
    hover_color = models.CharField(
        default="#000000", blank=False, null=False, max_length=500
    )
    background_color = models.CharField(
        default="#fafafa", blank=False, null=False, max_length=500
    )
    clientIcon = models.ImageField(
        blank=True, upload_to="settings/client_icon/"
    )
    videoInPage = models.FileField(
        blank=True, upload_to="settings/client/video/"
    )
    brandImage = models.ImageField(
        blank=True, upload_to="settings/client/brand_image/"
    )
    underPriceImage = models.ImageField(
        blank=True, upload_to="settings/client/underprice_image/"
    )
    # region PREFERENZE
    price_label = models.CharField(
        blank=False, null=False, default="€", max_length=8
    )
    piece_label = models.CharField(
        blank=False, null=False, default="pz.", max_length=16
    )
    gr_label = models.CharField(
        blank=False, null=False, default="gr.", max_length=16
    )
    hectogram_label = models.CharField(
        blank=False, null=False, default="etto/i", max_length=16
    )
    kg_label = models.CharField(
        blank=False, null=False, default="Kg.", max_length=16
    )
    kg_price_label = models.CharField(
        blank=False, null=False, default="al Kg.", max_length=16
    )
    hectogram_price_label = models.CharField(
        blank=False, null=False, default="l'etto", max_length=16
    )
    # endregion

    class Meta:
        verbose_name = "Impostazioni cliente"
        verbose_name_plural = "Impostazioni clienti"


class PolotnoToken(Token):
    interactive_flyer = models.OneToOneField(
        "builder.InteractiveFlyer",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="polotno_token",
    )

    TYPE_CHOICES = [  # todo aggiungi altri tipi
        ("4", "index"),
        ("ogImageMeta", "ogImageMeta"),
        ("ogImageMeta_mobile", "ogImageMeta_mobile"),
        ("clientIcon", "clientIcon"),
        ("category_banner", "category_banner"),
        ("category_banner_mobile", "category_banner_mobile"),
        ("brandImage", "brandImage"),
        ("clientIconLOW", "clientIconLOW"),
        ("product_banner", "product_banner"),
        ("Volantino A4", "Volantino A4"),
        ("Volantino quadrato", "Volantino quadrato"),
    ]
    type = models.CharField(
        max_length=32, choices=TYPE_CHOICES, blank=True, null=True
    )

    ACTION_CHOICES = [
        ("new", "new"),
        ("upd", "upd"),
    ]
    action = models.CharField(
        max_length=32, choices=ACTION_CHOICES, blank=True, null=True
    )
    id_template = models.IntegerField(blank=True, null=True)
    id_format = models.IntegerField(blank=True, null=True)
    tab_id = models.CharField(max_length=100, blank=True, null=True)
