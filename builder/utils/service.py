from uuid import uuid4

from django.utils.crypto import get_random_string


def interactive_flyer_flyer_pdf_file_directory_path(instance, filename):
    return f"{instance.assets_token}/pdf/{filename}"


def interactive_flyer_flyer_json_file_directory_path(instance, filename):
    return f"{instance.assets_token}/json/{filename}"


def interactive_flyer_page_image_file_directory_path(instance, filename):
    return f"{instance.interactive_flyer.assets_token}/pages/{filename}"


def aws_uploader_path(instance, filename):
    return f"{instance.assets_token}/pages/{filename}"


def interactive_flyer_thumb_page_image_file_directory_path(instance, filename):
    return f"{instance.interactive_flyer.assets_token}/pages/thumbs/{filename}"


def interactive_flyer_video_interactivity_file_directory_path(
    instance, filename
):
    if instance.interactive_flyer_product.interactive_flyer_page is not None:
        assets_token = (
            instance.interactive_flyer_product.interactive_flyer_page.interactive_flyer.assets_token
        )
    else:
        assets_token = (
            instance.interactive_flyer_product.interactive_flyer.assets_token
        )

    return f"{assets_token}/video/{filename}"


def interactive_flyer_image_interactivity_file_directory_path(
    instance, filename
):
    if (
        instance.product_marker.interactive_flyer_product.interactive_flyer_page
        is not None
    ):
        assets_token = (
            instance.product_marker.interactive_flyer_product.interactive_flyer_page.interactive_flyer.assets_token
        )
    else:
        assets_token = (
            instance.product_marker.interactive_flyer_product.interactive_flyer.assets_token
        )

    return f"{assets_token}/images/{filename}"


def product_image_image_file_directory_path(instance, filename):
    if instance.interactive_flyer_product.interactive_flyer_page is not None:
        assets_token = (
            instance.interactive_flyer_product.interactive_flyer_page.interactive_flyer.assets_token
        )
    else:
        assets_token = (
            instance.interactive_flyer_product.interactive_flyer.assets_token
        )

    return f"{assets_token}/products/{filename}"


def generate_token():
    return uuid4().hex


def generate_product_uid():
    random_uid = get_random_string(length=10, allowed_chars="0123456789")
    return f"cstm{random_uid}"


def populate_project_settings_from_client_settings(client_setting, flyer):
    from builder.models import ProjectSetting

    project_setting = ProjectSetting.objects.create(
        interactive_flyer=flyer,
        client_id=client_setting.client_id,
        signboard_id=client_setting.signboard_id,
        release_id=client_setting.release_id,
    )
    project_setting.primary_color = client_setting.primary_color
    project_setting.secondary_color = client_setting.secondary_color
    project_setting.tertiary_color = client_setting.tertiary_color
    project_setting.hover_color = client_setting.hover_color
    project_setting.clientIcon = client_setting.clientIcon
    project_setting.videoInPage = client_setting.videoInPage
    project_setting.brandImage = client_setting.brandImage
    project_setting.underPriceImage = client_setting.underPriceImage

    project_setting.piece_label = client_setting.piece_label
    project_setting.price_label = client_setting.price_label
    project_setting.gr_label = client_setting.gr_label
    project_setting.hectogram_label = client_setting.hectogram_label
    project_setting.kg_label = client_setting.kg_label
    project_setting.kg_price_label = client_setting.kg_price_label
    project_setting.hectogram_price_label = (
        client_setting.hectogram_price_label
    )

    return project_setting
