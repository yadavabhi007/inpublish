from io import BytesIO

from aeb.connectors.connector import Connector
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext as _
from django_cleanup import cleanup
from rest_framework.renderers import JSONRenderer
from storages.backends.s3boto3 import S3Boto3Storage

from builder.utils.service import (
    interactive_flyer_flyer_pdf_file_directory_path,
    interactive_flyer_flyer_json_file_directory_path,
    interactive_flyer_page_image_file_directory_path,
    interactive_flyer_video_interactivity_file_directory_path,
    interactive_flyer_image_interactivity_file_directory_path,
    product_image_image_file_directory_path,
    generate_product_uid,
)


class Affiliate(models.Model):
    name = models.CharField(max_length=100, null=False, blank=False)
    seller_id = models.IntegerField(
        null=True, blank=True, verbose_name="Related seller ID"
    )

    # TODO
    """
    def seller(self):
        try:
            return Seller.objects.get(pk=self.seller_id)
        except Seller.DoesNotExist:
            return None

    def __str__(self):
        seller_name = self.seller().name if (
                self.seller() is not None) else "NOT SET!"
        return f"{self.name} (seller: {seller_name})"
    """


class InteractiveFlyer(models.Model):
    name = models.CharField(
        max_length=100,
        null=False,
        blank=False,
        verbose_name="InteractiveFlyer name",
    )

    DRAFT = 0
    PUBLISHED = 1
    SCHEDULED = 2
    TO_CORRECT = 3
    EXPIRED = 4
    ERROR = 5
    FORCED_CLOSURE = 6
    TRASH = 7
    WAIT_POLOTNO_PDF = 8
    SCHEDULED_FROM_PUBLISHED = 9

    STATUS_CHOICES = [
        (DRAFT, _("Bozza")),
        (PUBLISHED, _("Pubblicato")),
        (SCHEDULED, _("Pianificato")),
        (TO_CORRECT, _("Da correggere")),
        (EXPIRED, _("Scaduto")),
        (ERROR, _("Errore")),
        (FORCED_CLOSURE, _("Chiusura forzata")),
        (TRASH, _("Cestinato")),
        (WAIT_POLOTNO_PDF, _("In attesa del PDF da Polotno")),
        (SCHEDULED_FROM_PUBLISHED, _("Pianificato da Pubblicato")),
    ]
    status = models.IntegerField(
        choices=STATUS_CHOICES, default=0, db_index=True
    )
    publication_url = models.URLField(null=True, blank=True, default=None)
    seller_id = models.IntegerField(
        null=True, blank=True, verbose_name="A&B Seller ID"
    )
    project_type = models.CharField(
        null=False,
        blank=True,
        default="internal",
        max_length=30,
        verbose_name="Connector type",
    )
    affiliate = models.ForeignKey(
        Affiliate,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="projects",
    )
    flyer_pdf_file = models.FileField(
        upload_to=interactive_flyer_flyer_pdf_file_directory_path,
        max_length=100,
        null=True,
        blank=True,
        storage=S3Boto3Storage(),
    )
    flyer_json_file = models.FileField(
        upload_to=interactive_flyer_flyer_json_file_directory_path,
        max_length=100,
        null=True,
        blank=True,
        storage=S3Boto3Storage(),
    )
    flyer_zip_file = models.FileField(
        upload_to="interactive_flyer_zip",
        max_length=100,
        null=True,
        blank=True,
        storage=S3Boto3Storage(),
    )
    initialization_in_progress = models.BooleanField(
        default=False, db_index=True
    )
    zip_generation_in_progress = models.BooleanField(default=False)
    zip_last_generation = models.DateTimeField(null=True, blank=True)
    assets_token = models.CharField(
        max_length=100, null=True, blank=True, unique=True
    )
    products_import_in_progress = models.BooleanField(default=False)
    products_imported = models.IntegerField(null=True, blank=True, default=0)
    initialization_error = models.BooleanField(default=False)
    initialization_error_message = models.TextField(null=True, blank=True)
    user = models.ForeignKey(
        "builder.CustomUser",
        null=False,
        blank=False,
        on_delete=models.DO_NOTHING,
        related_name="flyers",
    )
    slug = models.SlugField(max_length=100, null=False, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    image_page_width = models.PositiveIntegerField(default=1200)
    image_page_height = models.PositiveIntegerField(default=1900)

    def save(self, *args, **kwargs):
        if self.slug == "" and self.status == self.PUBLISHED:
            self.slug = slugify(self.name)
        super(InteractiveFlyer, self).save(*args, **kwargs)

    def has_pages(self):
        return self.pages.filter(number__gt=0).count() > 0

    def num_pages(self):
        try:
            return self.pages.filter(number__gt=0).count()
        except:
            return 0

    def is_draft(self):
        return self.status == self.DRAFT

    def is_expired(self):
        return self.status == self.EXPIRED

    def is_scheduled(self):
        return self.status == self.SCHEDULED

    def is_published(self):
        return self.status == self.PUBLISHED

    def is_scheduled_from_published(self):
        return self.status == self.SCHEDULED_FROM_PUBLISHED

    def is_error(self):
        return self.status == self.ERROR

    def is_to_correct(self):
        return self.status == self.TO_CORRECT

    def is_forced_closure(self):
        return self.status == self.FORCED_CLOSURE

    def project_items(self, user_id):
        projects = []
        for project in self.projects.all():
            projects.append(project.get_project())

        connector = Connector(connector=self.project_type)
        if self.project_type == settings.USER_TYPE_AEB:
            id_client = self.seller_id
        elif self.project_type == settings.USER_TYPE_INTERNAL:
            id_client = user_id

        # TODO per ora ci sta unico progetto collegato
        return connector.get_products_campaign(id_client, projects[0]["id"])

    def save_json_file(self):
        self.flyer_json_file.delete()
        from builder.serializers import InteractiveFlyerSerializer

        serializer = InteractiveFlyerSerializer(self)
        json = JSONRenderer().render(serializer.data)
        io = BytesIO(json)
        self.flyer_json_file.save(
            f"{self.name}.json", content=ContentFile(io.getvalue())
        )

    def generate_zip(self):
        return True

    def categories(self):
        products = InteractiveFlyerProduct.objects.filter(
            interactive_flyer_page__interactive_flyer=self
        ).all()
        categories = {}
        for product in products:
            if (product.category_name is not None) and (product.category_name):
                if not product.category_name in categories:
                    categories[product.category_name] = []
            if (
                product.subcategory_name is not None
            ) and product.subcategory_name:
                if (
                    not product.subcategory_name
                    in categories[product.category_name]
                ):
                    categories[product.category_name].append(
                        product.subcategory_name
                    )

        categories_to_return = []
        for category in categories:
            categories_to_return.append(
                {
                    "category_name": category,
                    "subcategories": categories[category],
                }
            )

        return categories_to_return

    def has_index(self):
        return hasattr(self, "index")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Volantino interattivo"
        verbose_name_plural = "Volantini interattivi"
        indexes = [
            models.Index(
                fields=["status", "created_at", "initialization_in_progress"]
            ),
        ]


class InteractiveFlyerProject(models.Model):
    interactive_flyer = models.ForeignKey(
        InteractiveFlyer, on_delete=models.CASCADE, related_name="projects"
    )
    project_id = models.IntegerField(
        null=True, blank=True, verbose_name="Related A&B project ID"
    )

    def get_project(self):
        try:
            connector = Connector(
                connector=self.interactive_flyer.project_type
            )
            proj = connector.get_campaign(
                self.interactive_flyer.seller_id, self.project_id
            )
            return proj
        except Exception:
            return None

    def __str__(self):
        try:
            return (
                self.get_project()["nome"]
                if (self.get_project() is not None)
                else "NOT SET!"
            )
        except:
            return "NOT SET!"


class InteractiveFlyerIndex(models.Model):
    interactive_flyer = models.OneToOneField(
        InteractiveFlyer, on_delete=models.CASCADE, related_name="index"
    )
    image_file = models.ImageField(
        upload_to=interactive_flyer_page_image_file_directory_path,
        max_length=100,
        null=True,
        blank=True,
        storage=S3Boto3Storage(),
    )
    thumb_image_file = models.ImageField(
        upload_to=interactive_flyer_page_image_file_directory_path,
        max_length=100,
        null=True,
        blank=True,
        storage=S3Boto3Storage(),
    )


class InteractiveFlyerIndexLink(models.Model):
    interactive_flyer_index = models.ForeignKey(
        InteractiveFlyerIndex, on_delete=models.CASCADE, related_name="links"
    )
    target = models.CharField(max_length=16, default="_blank")
    url = models.CharField(max_length=256, default="", blank=True, null=True)
    title = models.CharField(
        max_length=128, blank=True, null=False, default=""
    )
    color = models.CharField(
        default="#000000", blank=False, null=False, max_length=12
    )

    TYPE_EXTERNAL_LINK = "url"
    TYPE_INTERNAL_LINK = "internal_link"
    TYPE_CHOICES = [
        (TYPE_EXTERNAL_LINK, "external_link"),
        (TYPE_INTERNAL_LINK, "internal_link"),
    ]
    type = models.CharField(
        max_length=16, default="internal_link", choices=TYPE_CHOICES
    )
    page = models.IntegerField()


class InteractiveFlyerPage(models.Model):
    interactive_flyer = models.ForeignKey(
        InteractiveFlyer, on_delete=models.CASCADE, related_name="pages"
    )
    number = models.IntegerField(db_index=True)
    image_file = models.URLField(blank=True, null=True, default=None)
    thumb_image_file = models.URLField(blank=True, null=True, default=None)
    json_page = models.JSONField(blank=False, null=True, default=None)

    def __str__(self):
        return f"page {self.number} - flyer: {self.interactive_flyer.name}"

    class Meta:
        ordering = ["number"]
        verbose_name = "Pagina interattive"
        verbose_name_plural = "Pagine interattive"
        indexes = [
            models.Index(fields=["number"]),
        ]


class InteractiveFlyerProduct(models.Model):
    # STATUS_CHOICES = [
    #     (0, 'pezzo'),
    #     (1, 'grammo'),
    #     (2, 'etto'),
    #     (3, 'kilo'),
    # ]

    principal_product = models.ForeignKey(
        "builder.InteractiveFlyerProduct",
        null=True,
        blank=True,
        default=None,
        on_delete=models.CASCADE,
        related_name="related",
    )
    interactive_flyer = models.ForeignKey(
        InteractiveFlyer,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="products",
    )
    interactive_flyer_page = models.ForeignKey(
        InteractiveFlyerPage,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="products",
    )

    ean_code = models.CharField(
        max_length=100, null=True, blank=True, verbose_name="Codice EAN"
    )
    # identificativo custom del cliente, è da generare solo se arriva vuoto
    codice_interno_insegna = models.CharField(
        max_length=100, null=True, blank=True, db_index=True
    )
    # id del database del prodotto
    product_uid = models.CharField(
        max_length=100, null=True, blank=True, verbose_name="Related item ID"
    )

    field1 = models.CharField(
        max_length=500, null=True, blank=True, default=""
    )
    field2 = models.CharField(
        max_length=500, null=True, blank=True, default=""
    )
    field3 = models.CharField(
        max_length=500, null=True, blank=True, default=""
    )
    field4 = models.CharField(
        max_length=500, null=True, blank=True, default=""
    )
    descrizione_estesa = models.TextField(null=True, blank=True, default=None)

    grammage = models.IntegerField(default=0, null=True, blank=True)
    price_with_iva = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=0.00,
        verbose_name="Price with IVA",
    )
    offer_price = models.DecimalField(
        blank=False,
        null=True,
        max_digits=10,
        decimal_places=2,
        default=None,
        verbose_name="Offer price",
    )
    calcolo_prezzo = models.IntegerField(default=1, blank=True, null=True)
    price_for_kg = models.DecimalField(
        max_digits=10, decimal_places=4, blank=True, null=True
    )
    available_pieces = models.PositiveIntegerField(
        default=1, blank=True, null=True
    )
    max_purchasable_pieces = models.PositiveSmallIntegerField(
        default=1, blank=True, null=True
    )
    punti = models.CharField(max_length=100, blank=True)
    fidelity_product = models.BooleanField(default=False)
    focus = models.BooleanField(default=False)
    pam = models.BooleanField(default=False)
    three_for_two = models.BooleanField(default=False)
    one_and_one_gratis = models.BooleanField(default=False)
    underpriced_product = models.BooleanField(default=False)

    category = models.CharField(max_length=200, blank=True, null=True)
    category_name = models.CharField(max_length=200, blank=True, null=True)
    subcategory = models.CharField(max_length=200, blank=True, null=True)
    subcategory_name = models.CharField(max_length=200, blank=True, null=True)

    equivalence = models.PositiveIntegerField(blank=True, null=True)
    quantity_step = models.PositiveIntegerField(blank=True, null=True)

    price_label = models.CharField(max_length=200, blank=True, null=True)
    grocery_label = models.CharField(max_length=200, blank=True, null=True)
    weight_unit_of_measure = models.CharField(
        max_length=20, blank=True, null=True
    )

    TYPE_PRODUCT = "product"
    TYPE_EXTERNAL_LINK = "external_link"
    TYPE_INTERNAL_LINK = "internal_link"
    TYPE_VIDEO = "video"
    TYPE_CHOICES_KEYS = [
        TYPE_PRODUCT,
        TYPE_EXTERNAL_LINK,
        TYPE_INTERNAL_LINK,
        TYPE_VIDEO,
    ]
    TYPE_CHOICES = [
        (TYPE_PRODUCT, "product"),
        (TYPE_EXTERNAL_LINK, "external_link"),
        (TYPE_INTERNAL_LINK, "internal_link"),
        (TYPE_VIDEO, "video"),
    ]
    type = models.CharField(
        max_length=100,
        choices=TYPE_CHOICES,
        blank=False,
        null=False,
        default="product",
    )

    # region campi giodicart
    sku = models.CharField(max_length=50, blank=True, null=True, default=None)
    strike_price = models.CharField(
        max_length=100, blank=True, null=True, default=None
    )
    discount_rate = models.DecimalField(
        blank=True, null=True, default=0.00, max_digits=10, decimal_places=4
    )
    prices = models.JSONField(blank=True, null=True, default=None)
    promo = models.BooleanField(blank=True, null=True, default=None)
    stock = models.CharField(max_length=5, blank=True, null=True, default=None)
    tdc = models.PositiveIntegerField(blank=True, null=True, default=None)
    available_from = models.CharField(
        max_length=100, blank=True, null=True, default=None
    )
    brand = models.CharField(
        max_length=100, blank=True, null=True, default=None
    )
    brand_logo = models.URLField(blank=True, null=True, default=None)
    line = models.CharField(
        max_length=100, blank=True, null=True, default=None
    )
    line_logo = models.URLField(blank=True, null=True, default=None)
    # endregion

    # "other": "" // altre informazioni sul prodotto
    # "oldPrice": "5,00", // prezzo di partenza del prodotto
    # "discount": "20%", // Sconto applicato al prodotto

    def get_categories(self):
        pass

    def varieties_list(self):
        return self.varieties.all().values_list("name", flat=True)

    def description(self):
        return " ".join(
            filter(None, [self.field1, self.field2, self.field3, self.field4])
        )

    def varieties_tokens(self):
        return ",".join(self.varieties.values_list("name", flat=True))

    def cropped_image_url(self):
        if self.images.filter(cropped=True).count() > 0:
            return self.images.filter(cropped=True)[0].image_file.url
        return ""

    def default_image_url(self):
        if self.images.all().count() > 0:
            return self.images.all()[0].image_file.url
        return ""

    def not_cropped_images(self):
        return self.images.filter(cropped=False).all()

    def has_link_interactivity(self):
        return self.markers.filter(type="world", active=True).count() > 0

    def has_video_interactivity(self):
        return self.markers.filter(type="play", active=True).count() > 0

    def has_recipe_interactivity(self):
        return self.markers.filter(type="hat-chef", active=True).count() > 0

    def has_info_interactivity(self):
        return self.markers.filter(type="info", active=True).count() > 0

    def has_specs_interactivity(self):
        return self.markers.filter(type="specs", active=True).count() > 0

    def save(self, *args, **kwargs):
        if not self.codice_interno_insegna:
            self.codice_interno_insegna = generate_product_uid()
            while InteractiveFlyerProduct.objects.filter(
                codice_interno_insegna=self.codice_interno_insegna
            ).exists():
                self.codice_interno_insegna = generate_product_uid()
        super(InteractiveFlyerProduct, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.description()} {self.codice_interno_insegna=}"

    class Meta:
        verbose_name = "Prodotto volantino interattivo"
        verbose_name_plural = "Prodotti volantino interattivo"
        indexes = [
            models.Index(fields=["codice_interno_insegna"]),
        ]


class InteractiveFlyerProductVariety(models.Model):
    interactive_flyer_product = models.ForeignKey(
        InteractiveFlyerProduct,
        on_delete=models.CASCADE,
        related_name="varieties",
    )
    name = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.name


class ProductBlueprint(models.Model):
    interactive_flyer_product = models.OneToOneField(
        InteractiveFlyerProduct,
        on_delete=models.CASCADE,
        related_name="blueprint",
    )
    top = models.FloatField(null=True, blank=False)
    left = models.FloatField(null=True, blank=False)
    width = models.FloatField(null=True, blank=False)
    height = models.FloatField(null=True, blank=False)


class IndexLinkBlueprint(models.Model):
    interactive_flyer_index_link = models.OneToOneField(
        InteractiveFlyerIndexLink,
        on_delete=models.CASCADE,
        related_name="blueprint",
    )
    top = models.FloatField(null=True, blank=False)
    left = models.FloatField(null=True, blank=False)
    width = models.FloatField(null=True, blank=False)
    height = models.FloatField(null=True, blank=False)


class ProductMarker(models.Model):
    interactive_flyer_product = models.ForeignKey(
        InteractiveFlyerProduct,
        on_delete=models.CASCADE,
        related_name="markers",
    )
    MARKER_TYPE_CHOICES = [
        ("plus", "plus"),  # marker sul prodotto
        ("world", "world"),  # link
        ("play", "play"),  # video
        ("hat-chef", "hat-chef"),  # ricetta
        ("info", "info"),  # informazioni
        ("specs", "specs"),  # specifiche
        ("external_link", "external_link"),  # link esterno
        ("internal_link", "internal_link"),  # link interno
    ]
    type = models.CharField(
        max_length=100,
        choices=MARKER_TYPE_CHOICES,
        blank=True,
        null=True,
        db_index=True,
    )
    data = models.CharField(max_length=100, blank=True, null=True)
    title = models.CharField(max_length=200, blank=True, null=True)
    link = models.CharField(max_length=200, blank=True, null=True)
    ingredients = models.TextField(null=True, blank=True)
    recipe = models.TextField(null=True, blank=True)
    content_title = models.CharField(max_length=200, blank=True, null=True)
    content_text = models.TextField(null=True, blank=True)
    specifications = models.TextField(null=True, blank=True)
    active = models.BooleanField(default=True, db_index=True)
    video_file = models.FileField(
        upload_to=interactive_flyer_video_interactivity_file_directory_path,
        max_length=100,
        null=True,
        blank=True,
        storage=S3Boto3Storage(),
    )

    page_number = models.PositiveIntegerField(default=0)
    show_icon = models.BooleanField(default=False)
    tooltip = models.CharField(max_length=100, blank=True, null=True)
    open_modal = models.BooleanField(default=False)
    VIDEO_TYPE_CHOICES = [
        ("youtube", "youtube"),
        ("video_file", "video_file"),
    ]
    video_type = models.CharField(
        max_length=100, choices=VIDEO_TYPE_CHOICES, blank=True, null=True
    )
    LINK_TYPE_CHOICES = [
        ("url", "url"),
        ("email", "email"),
        ("telephone", "telephone"),
    ]
    link_type = models.CharField(
        max_length=100, choices=LINK_TYPE_CHOICES, blank=True, null=True
    )
    color = models.CharField(
        default="#000000", blank=False, null=False, max_length=500
    )

    class Meta:
        indexes = [
            models.Index(fields=["active", "type"]),
        ]

    def __str__(self):
        return f"{self.interactive_flyer_product.field1} - {self.type}"


class ProductMarkerImage(models.Model):
    product_marker = models.ForeignKey(
        ProductMarker, on_delete=models.CASCADE, related_name="images"
    )
    image_file = models.ImageField(
        upload_to=interactive_flyer_image_interactivity_file_directory_path,
        max_length=100,
        null=True,
        blank=True,
        storage=S3Boto3Storage(),
    )


class ProductImage(models.Model):
    interactive_flyer_product = models.ForeignKey(
        InteractiveFlyerProduct,
        on_delete=models.CASCADE,
        related_name="images",
    )
    image_file = models.ImageField(
        upload_to=product_image_image_file_directory_path,
        max_length=100,
        null=True,
        blank=True,
        storage=S3Boto3Storage(),
    )
    cropped = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = [
            "cropped",
        ]
        indexes = [
            models.Index(fields=["cropped"]),
        ]


@cleanup.ignore
class ProjectSetting(models.Model):
    interactive_flyer = models.OneToOneField(
        InteractiveFlyer, on_delete=models.CASCADE, related_name="settings"
    )
    # region CONFIGURAZIONE
    PAGER_BUTTONS = "buttons"
    PAGER_SLIDER = "slider"
    PAGER_INDEX = "index"
    PAGER_CHOICES = [
        (PAGER_BUTTONS, _("Bottoni")),
        (PAGER_SLIDER, _("Slider")),
        (PAGER_INDEX, _("Indice")),
    ]
    pager = models.CharField(
        max_length=32, choices=PAGER_CHOICES, default="buttons"
    )
    sidebar = models.JSONField(default=list)
    send_grocery_list_to_market = models.BooleanField(
        null=False, default=False
    )
    grocery_list_min_value = models.IntegerField(default=0)
    has_pages = models.BooleanField(null=False, default=True)
    hide_grocery_list = models.BooleanField(null=False, default=True)
    hide_searchbar = models.BooleanField(null=False, default=True)
    category_banner = models.ImageField(
        blank=True, upload_to="settings/project/category_banner/"
    )
    category_banner_mobile = models.ImageField(
        blank=True, upload_to="settings/project/category_banner_mobile/"
    )
    hide_plus_product = models.BooleanField(null=False, default=False)
    hide_plus_product_price = models.BooleanField(null=False, default=False)
    show_list_check = models.BooleanField(null=False, default=False)
    show_right_index = models.BooleanField(null=False, default=False)
    manager_stock = models.BooleanField(null=False, default=False)
    hide_listPages = models.BooleanField(null=False, default=False)
    TYPE_CHOICES = [
        ("leaflet", "Volantino"),
        ("catalog", "Catalogo"),
        ("menu", "Menù"),
        ("magazine", "Magazine"),
        ("e-book", "E-Book"),
    ]
    FORMAT_CHOICES = [
        ("1", "Footer large"),
        ("2", "Header large"),
        ("3", "Header small"),
        ("4", "Indice template"),
        ("5", "Catalogo A4"),
        ("6", "Catalogo Template"),
        ("7", "clientIcon"),
        ("8", "ogImageMeta"),
        ("9", "ogImageMeta_mobile"),
        ("10", "category_banner"),
        ("11", "category_banner_mobile"),
        ("12", "product_banner"),
        ("13", "Volantino A4"),
        ("14", "Volantino quadrato"),
        ("15", "Indice A4"),
        ("16", "Indice quadrato"),
        ("17", "Grafica condivisione Facebook"),
        ("18", "logo_full"),
    ]
    type = models.CharField(
        max_length=30, choices=TYPE_CHOICES, default="leaflet"
    )
    format = models.CharField(
        max_length=30, choices=FORMAT_CHOICES, default="leaflet"
    )
    no_link_to_site = models.BooleanField(null=False, default=False)
    ICONANIMATION_CHOICES = [
        ("", "Fissa"),
        ("verticalListaSpesa", "Salto"),
        ("vertical", "Scomparsa"),
    ]
    iconAnimation = models.CharField(
        default="",
        max_length=24,
        choices=ICONANIMATION_CHOICES,
        null=False,
        blank=True,
    )
    largeIcon = models.BooleanField(null=False, default=False)
    hide_logo = models.BooleanField(null=False, default=False)
    small_logo = models.BooleanField(null=False, default=False)
    only_browsable = models.BooleanField(null=False, default=False)
    show_one_page = models.BooleanField(null=False, default=False)
    version = models.IntegerField(default=0)
    filterBrand = models.IntegerField(default=0)
    filterUnderprice = models.IntegerField(default=0)
    marker_product_in_list = models.BooleanField(default=False)
    MARKER_CHOICES = [
        ("ellipse_black", "ellipse_black"),
        ("circle_black", "circle_black"),
        ("circle_blue", "circle_blue"),
        ("highlighted_yellow", "highlighted_yellow"),
    ]
    marker = models.CharField(
        max_length=32, choices=MARKER_CHOICES, default=None, null=True
    )
    # endregion
    # region DATI CLIENTE
    client_id = models.IntegerField()
    signboard_id = models.IntegerField()
    release_id = models.IntegerField()
    # endregion
    # region pubblication fields
    publicationDate = models.DateTimeField(
        blank=True, null=True, default=None, db_index=True
    )
    expirationDate = models.DateTimeField(
        blank=True, null=True, default=None, db_index=True
    )
    # endregion
    # region GRAFICA
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
        blank=True, upload_to="settings/project/client_icon/"
    )
    logo_full = models.ImageField(
        null=True, blank=True, upload_to="settings/project/logo_full/"
    )
    videoInPage = models.FileField(
        blank=True, upload_to="settings/project/video/"
    )
    brandImage = models.ImageField(
        blank=True, upload_to="settings/project/brand_image/"
    )
    underPriceImage = models.ImageField(
        blank=True, upload_to="settings/project/underprice_image/"
    )
    # endregion
    # region SEO
    shareFlyerTitle = models.CharField(
        default="", blank=True, null=False, max_length=500
    )
    shareFlyerURL = models.CharField(
        default="", blank=True, null=False, max_length=500
    )
    shareProductSentence = models.CharField(
        default="", blank=True, null=False, max_length=500
    )
    ogTitleMeta = models.CharField(
        default="", blank=True, null=False, max_length=500
    )
    ogDescriptionMeta = models.CharField(
        default="", blank=True, null=False, max_length=500
    )
    ga_active = models.BooleanField(default=True)
    ga_tracking_id = models.CharField(
        default="", blank=True, null=True, max_length=500
    )
    # endregion
    # region CONDIVISIONE
    ogImageMeta = models.ImageField(
        blank=True, upload_to="settings/project/image_meta/"
    )
    ogImageMeta_mobile = models.ImageField(
        blank=True, upload_to="settings/project/image_meta_mobile/"
    )
    # endregion
    # region OPZIONI BANNER
    internal_banner_click = models.BooleanField(null=False, default=False)
    external_banner_click = models.BooleanField(null=False, default=False)
    product_banner = models.ForeignKey(
        InteractiveFlyerProduct,
        blank=True,
        null=True,
        default=None,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    href_banner = models.CharField(blank=True, null=True, max_length=500)
    # endregion
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
        verbose_name = "Impostazioni volantino"
        verbose_name_plural = "Impostazioni volantini"
        indexes = [
            models.Index(fields=["expirationDate", "publicationDate"]),
        ]
