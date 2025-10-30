from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from ecommerce_app import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin Panel
    path("admin/", admin.site.urls),

    # --- API ROUTES ---
    # All API endpoints from ecommerce_app (Register, Login, Products, Cart, Orders)
    path("api/", include("ecommerce_app.urls")),

    # --- UI ROUTES ---
    # Template-based routes for visual pages
    path("", TemplateView.as_view(template_name="e-com/home.html"), name="home"),
    path("ui/register/", TemplateView.as_view(template_name="e-com/register.html"), name="ui_register"),
    path("ui/login/", TemplateView.as_view(template_name="e-com/login.html"), name="ui_login"),
    path("ui/add_product/", TemplateView.as_view(template_name="e-com/add_product.html"), name="ui_add_product"),
    # path("ui/product_list/", TemplateView.as_view(template_name="e-com/product_list.html"), name="ui_product_list"),
    path("ui/cart/", TemplateView.as_view(template_name="e-com/cart.html"), name="ui_cart"),
    path("ui/orders/", TemplateView.as_view(template_name="e-com/orders.html"), name="ui_orders"),
    path("ui/order_detail/", TemplateView.as_view(template_name="e-com/order_detail.html"), name="ui_order_detail"),
    path("ui/forget_password/", TemplateView.as_view(template_name="e-com/forget_password.html"), name="ui_forget_password"),
    path("ui/reset_password/", TemplateView.as_view(template_name="e-com/reset_password.html"), name="ui_reset_password"),
    path("ui/verify_otp/", TemplateView.as_view(template_name="e-com/verify_otp.html"), name="ui_verify_otp"),
    path("ui/all_product/", TemplateView.as_view(template_name="e-com/ViewAllProducts.html"), name="ui_all_product"),
    path("ui/product_list/", views.ProductListView.as_view(), name="ui_product_list"),

]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
