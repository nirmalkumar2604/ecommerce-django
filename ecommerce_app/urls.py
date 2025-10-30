# ecommerce_app/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("forget_password/", views.ForgetPasswordView.as_view(), name="forget_password"),
    path("reset_password/", views.ResetPasswordView.as_view(), name="reset_password"),
    path("verify_otp/", views.VerifyOTPView.as_view(), name="verify_otp"),

    # Product Management
    path("add_product/", views.AddProductView.as_view(), name="add_product"),
    path("edit_product/<int:pk>/", views.EditProductView.as_view(), name="edit_product"),
    path("delete_product/<int:pk>/", views.DeleteProductView.as_view(), name="delete_product"),
    path("view_all_products/", views.ViewAllProducts.as_view(), name="view_all_products"),



    # Cart Management
    path("add_to_cart/", views.Addproducttocartview.as_view(), name="add_to_cart"),
    path("view_cart/", views.ViewCartView.as_view(), name="view_cart"),
    path("edit_cart/", views.Editcartview.as_view(), name="edit_cart"),
    path("delete_cart/", views.Deleteitemincartview.as_view(), name="delete_cart"),

    # Orders
    path("place_order/", views.PlaceOrderView.as_view(), name="place_order"),
    path("order_list/", views.Orderlistview.as_view(), name="order_list"),
    path("order_detail/<int:pk>/", views.Orderdetailview.as_view(), name="order_detail"),

    # Addresses
    path("add_address/", views.AddressCreateView.as_view(), name="add_address"),
    path("address_list/", views.AddressListView.as_view(), name="address_list"),
    path("address_delete/",views.AddressDeleteView.as_view(), name="address_delete"),

    # Coupons & Notifications
    path("apply_coupon/", views.CouponApplyView.as_view(), name="apply_coupon"),
    path("Coupon_Remove/", views.CouponRemoveView.as_view(), name="coupon_remove"),
    path("notifications/", views.NotificationListView.as_view(), name="notifications"),
]

