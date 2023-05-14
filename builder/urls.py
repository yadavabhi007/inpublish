from django.urls import path
from builder import views
from django.contrib.auth import views as auth_views

app_name = "builder"

urlpatterns = [
    path(
        "",
        auth_views.LoginView.as_view(redirect_authenticated_user=True),
        name="login",
    ),
    path("new-user/", views.NewUserView.as_view(), name="new_user"),
    path(
        "auth-token/",
        views.AuthWithTokenView.as_view(),
        name="auth_with_token",
    ),
    path("error-page/", views.ErrorPageView.as_view(), name="error_page"),
    path(
        "session-expired/",
        views.ErrorPageView.as_view(),
        name="session_expired",
    ),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("dashboard", views.DashboardView.as_view(), name="dashboard"),
    path(
        "setting/client/",
        views.SettingClientView.as_view(),
        name="setting_client",
    ),
    path(
        "interactive-flyers/<int:interactive_flyer_id>/settings/",
        views.InteractiveFlyerSettingsView.as_view(),
        name="interactive_flyer_settings",
    ),
    path(
        "interactive-flyers/<int:interactive_flyer_id>/delete/",
        views.DeleteInteractiveFlyerView.as_view(),
        name="delete_interactive_flyer",
    ),
    path(
        "interactive-flyer/<int:interactive_flyer_id>/share/",
        views.ShareFlyerView.as_view(),
        name="share_flyer",
    ),
    path(
        "interactive-flyer/new/",
        views.CreateInteractiveFlyer.as_view(),
        name="new_interactive_flyer",
    ),
    path(
        "seller-affiliates-select",
        views.SellerAffiliatesSelectView.as_view(),
        name="seller_affiliates_select",
    ),
    path(
        "seller-projects-select",
        views.SellerProjectsSelect.as_view(),
        name="seller_projects_select",
    ),
    path(
        "interactive-flyer/<int:interactive_flyer_id>/edit/",
        views.EditInteractiveFlyer.as_view(),
        name="edit_interactive_flyer",
    ),
    path(
        "interactive-flyer/<int:interactive_flyer_id>/preview/",
        views.InteractiveFlyerPrevewView.as_view(),
        name="preview_interactive_flyer",
    ),
    path(
        "interactive-flyer/<int:interactive_flyer_id>/<str:new_state>/",
        views.ManagePublicationInteractiveFlyer.as_view(),
        name="manage_publication_interactive_flyer",
    ),
    # region gestione indice
    path(
        "interactive-flyer/<int:interactive_flyer_id>/index/create",
        views.InteractiveFlyerCreateIndexView.as_view(),
        name="interactive_flyer_create_index",
    ),
    # endregion
    path(
        "interactive-flyer-json/<int:interactive_flyer_id>",
        views.InteractiveFlyerJsonView.as_view(),
        name="interactive_flyer_json",
    ),
    # region api
    path(
        "api/interactive-flyers/<int:interactive_flyer_id>/zip-generation-status/",
        views.ZipGenerationStatusView.as_view(),
        name="interactive_flyer_zip_generation_status",
    ),
    path(
        "api/interactive-flyer/<int:interactive_flyer_id>/receive-pages/",
        views.ReceivePagesView.as_view(),
        name="interactive_flyer_receive_pages",
    ),
    # api pagine
    path(
        "api/interactive-flyers/<int:interactive_flyer_id>/page/<int:page_number>/delete/",
        views.InteractiveFlyerDeletePageView.as_view(),
        name="interactive_flyer_delete_page",
    ),
    path(
        "api/interactive-flyer/<int:interactive_flyer_id>/page/<int:page_number>/products/",
        views.InteractiveFlyerProductsPageView.as_view(),
        name="get_interactive_flyer_products_page_api",
    ),
    # endregion
    path(
        "api/interactive-flyer/products/archive/",
        views.InteractiveFlyerProductsArchiveView.as_view(),
        name="interactive_flyer_archive_products",
    ),
    path(
        "api/interactive-flyer/<int:interactive_flyer_id>/products/campaign/",
        views.InteractiveFlyerProjectItemsView.as_view(),
        name="interactive_flyer_project_items",
    ),
    path(
        "api/subcategories-by-category/<int:category_id>/",
        views.SubcategoriesByCategoryView.as_view(),
        name="subcategories_by_category",
    ),
    path(
        "api/interactive-flyers",
        views.InteractiveFlyersJsonView.as_view(),
        name="filtered_interactive_flyers_json",
    ),
    path(
        "api/interactive-flyers/all",
        views.InteractiveFlyersJsonView.as_view(),
        name="all_interactive_flyers_json",
    ),
    path(
        "api/interactive-flyer/<int:interactive_flyer_id>/detail/",
        views.InteractiveFlyerDetailJsonView.as_view(),
        name="interactive_flyer_json",
    ),
    path(
        "api/interactive-flyer/<int:interactive_flyer_id>/product/campaign/<int:product_id>/",
        views.GetProductCampaignView.as_view(),
        name="get_product_campaign_api",
    ),
    path(
        "api/product/archive/<int:product_id>/",
        views.GetProductArchiveView.as_view(),
        name="get_product_archive_api",
    ),
    # region api prodotti
    path(
        "api/interactive-flyer/<int:interactive_flyer_id>/product/giodicart/create/",
        views.CreateGiodicartProductView.as_view(),
        name="create_giodicart_product",
    ),
    path(
        "api/interactive-flyer/<int:interactive_flyer_id>/product/giodicart/<int:product_id>/update/",
        views.UpdateGiodicartProductView.as_view(),
        name="update_giodicart_product",
    ),
    path(
        "api/interactive-flyer/<int:interactive_flyer_id>/product/create/",
        views.InteractiveFlyerCreateProductView.as_view(),
        name="interactive_flyer_create_product",
    ),
    path(
        "api/interactive-flyer/<int:interactive_flyer_id>/product/<int:product_id>/update/",
        views.InteractiveFlyerEditProductView.as_view(),
        name="interactive_flyer_update_product",
    ),
    path(
        "api/interactive-flyer/<int:interactive_flyer_id>/product/<int:product_id>/delete/",
        views.InteractiveFlyerDeleteProductView.as_view(),
        name="interactive_flyer_delete_product",
    ),
    # endregion
    # region api immagini prodotti
    path(
        "api/interactive-flyer/<int:interactive_flyer_id>/product/<int:product_id>/images/",
        views.GetProductImagesView.as_view(),
        name="get_interactive_flyer_product_images_api",
    ),
    path(
        "api/interactive-flyer/<int:interactive_flyer_id>/product/<int:product_id>/image/create/",
        views.InteractiveFlyerCreateProductImageView.as_view(),
        name="interactive_flyer_create_product_image_api",
    ),
    path(
        "api/interactive-flyer/<int:interactive_flyer_id>/product/<int:product_id>/image/<int:image_id>/delete/",
        views.InteractiveFlyerDeleteProductImageView.as_view(),
        name="interactive_flyer_product_image_delete_api",
    ),
    # endregion
    # region api indice
    path(
        "api/interactive-flyer/<int:interactive_flyer_id>/index/link/",
        views.InteractiveFlyerIndexLinksView.as_view(),
        name="interactive_flyer_index_links_api",
    ),
    path(
        "api/interactive-flyer/<int:interactive_flyer_id>/index/delete/",
        views.InteractiveFlyerIndexDeleteView.as_view(),
        name="interactive_flyer_delete_index_api",
    ),
    path(
        "api/interactive-flyer/<int:interactive_flyer_id>/index/link/create/",
        views.InteractiveFlyerCreateIndexLinkView.as_view(),
        name="interactive_flyer_create_index_link_api",
    ),
    path(
        "api/interactive-flyer/<int:interactive_flyer_id>/index/link/<int:link_id>/edit/",
        views.InteractiveFlyerEditIndexLinkView.as_view(),
        name="interactive_flyer_edit_index_link_api",
    ),
    path(
        "api/interactive-flyer/<int:interactive_flyer_id>/index/link/<int:link_id>/delete/",
        views.InteractiveFlyerDeleteIndexLinkView.as_view(),
        name="interactive_flyer_delete_index_link_api",
    ),
    # endregion
    path(
        "api/interactive-flyer/<int:interactive_flyer_id>/product/<int:product_id>/"
        "interactivity/<str:interaction_type>/",
        views.InteractiveFlyerProductInteractivityView.as_view(),
        name="interactive_flyer_product_interactivity_api",
    ),
    path(
        "api/interactive-flyer/<int:interactive_flyer_id>/interactivity/<str:interaction_type>/",
        views.InteractiveFlyerInteractivityView.as_view(),
        name="interactive_flyer_interactivity_api",
    ),
    path(
        "api/interactive-flyer/<int:interactive_flyer_id>/price/labels/",
        views.GetPriceLabelsApiView.as_view(),
        name="get_price_labels_api",
    ),
    path(
        "api/permissions/",
        views.PermissionsApiView.as_view(),
        name="get_permissions_api",
    ),
    # region polotno integration api
    path(
        "api/polotno/auth/",
        views.PolotnoAuthView.as_view(),
        name="polotno_auth_api",
    ),
    path("api/polotno/", views.PolotnoView.as_view(), name="polotno_api"),
    # endregion
    path(
        "api/giodicart/product/search/",
        views.GiodicartSearchProductView.as_view(),
        name="search_giodicart_product_api",
    ),
    # endregion
    path(
        "api/product/search/",
        views.SearchProductView.as_view(),
        name="search_product_api",
    ),
]
