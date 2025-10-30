from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.conf import settings
from decimal import Decimal
from django.views.generic import TemplateView
from datetime import datetime
from django.shortcuts import render
from django.views import View


def year_context(request):
    return {'year': datetime.now().year}


from .models import (
    Product, Cart, Order, OrderItem, Address, Notification, PasswordResetOTP
)

# ─────────────────────────────
# Auth
# ─────────────────────────────

class RegisterView(APIView):
    def post(self, request):
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')
        password2 = request.data.get('password2')

        if not all([username, email, password, password2]):
            return Response({"error": "All fields are required."}, status=status.HTTP_400_BAD_REQUEST)
        if password != password2:
            return Response({"error": "Passwords do not match."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            validate_email(email)
        except ValidationError:
            return Response({"error": "Invalid email address."}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(username=username).exists():
            return Response({"error": "Username already taken."}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(email=email).exists():
            return Response({"error": "Email already registered."}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(username=username, email=email, password=password)
        return Response({"message": "User registered successfully!", "user_id": user.id}, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        if not all([username, password]):
            return Response({"error": "Username and password are required."}, status=status.HTTP_400_BAD_REQUEST)
        user = authenticate(request, username=username, password=password)
        if user is None:
            return Response({"error": "Invalid username or password."}, status=status.HTTP_401_UNAUTHORIZED)
        return Response({"message": "Login successful!", "user_id": user.id}, status=status.HTTP_200_OK)
    

class logoutview(APIView):
    def post(self, request):
        # Invalidate session or token here if using token-based auth
        return Response({"message": "Logout successful!"}, status=status.HTTP_200_OK)    

# ─────────────────────────────
# Password reset via OTP
# ─────────────────────────────

class ForgetPasswordView(APIView):
    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({"error": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            validate_email(email)
        except ValidationError:
            return Response({"error": "Invalid email address."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "Email not found."}, status=status.HTTP_404_NOT_FOUND)

        import random
        otp = f"{random.randint(100000, 999999)}"

        PasswordResetOTP.objects.update_or_create(user=user, defaults={"otp": otp})

        send_mail(
            subject="Password Reset OTP",
            message=f"Your OTP for password reset is: {otp}. It is valid for 15 minutes.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        return Response({"message": "OTP has been sent to your email."}, status=status.HTTP_200_OK)


class VerifyOTPView(APIView):
    def post(self, request):
        email = request.data.get('email')
        otp = request.data.get('otp')
        if not all([email, otp]):
            return Response({"error": "Email and OTP are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            otp_obj = PasswordResetOTP.objects.get(user=user)  # OneToOne
        except PasswordResetOTP.DoesNotExist:
            return Response({"error": "No OTP found for this user."}, status=status.HTTP_404_NOT_FOUND)

        if otp_obj.is_expired():
            return Response({"error": "OTP expired. Please request a new one."}, status=status.HTTP_400_BAD_REQUEST)
        if otp_obj.otp != str(otp):
            return Response({"error": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"message": "OTP verified successfully."}, status=status.HTTP_200_OK)


# from django.contrib.auth.models import User
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status

class ResetPasswordView(APIView):
    def post(self, request):
        email = request.data.get("email")
        new_password = request.data.get("new_password")
        new_password2 = request.data.get("new_password2")

        # Step 1: Validate email field
        if not email:
            return Response({"error": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Step 2: Find user by email (case-insensitive)
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return Response({"error": "Email not found."}, status=status.HTTP_404_NOT_FOUND)

        # Step 3: Confirm password fields match
        if new_password != new_password2:
            return Response({"error": "Passwords do not match."}, status=status.HTTP_400_BAD_REQUEST)

        # Step


# ─────────────────────────────
# Profile & User delete
# ─────────────────────────────

class UserProfileView(APIView):
    def get(self, request):
        user_id = request.query_params.get('user_id')
        if not user_id:
            if request.user and request.user.is_authenticated:
                user = request.user
            else:
                return Response({"error": "User ID is required or authenticate to get your profile."},
                                status=status.HTTP_400_BAD_REQUEST)
        else:
            try:
                user = User.objects.get(id=int(user_id))
            except (User.DoesNotExist, ValueError, TypeError):
                return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        data = {"username": user.username, "email": user.email}
        return Response({"user_profile": data}, status=status.HTTP_200_OK)


class Deleteuserview(APIView):
    def delete(self, request):
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({"error": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(id=int(user_id))
        except (User.DoesNotExist, ValueError, TypeError):
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        user.delete()
        return Response({"message": "User deleted successfully."}, status=status.HTTP_200_OK)

# ─────────────────────────────
# Products
# ─────────────────────────────
class AddProductView(APIView):
    def post(self, request):
        name = request.data.get('name')
        price = request.data.get('price')
        description = request.data.get('description', "")
        category = request.data.get('category', "")
        stock = request.data.get('stock', 0)
        image = request.data.get('image', "")  # ✅ Accept image URL

        if not all([name, price]):
            return Response({"error": "name and price are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            price = Decimal(str(price))
            stock = int(stock)
        except (ValueError, TypeError):
            return Response({"error": "Invalid price or stock."}, status=status.HTTP_400_BAD_REQUEST)

        product = Product.objects.create(
            name=name,
            price=price,
            description=description,
            category=category,
            stock=stock,
            image=image,  # ✅ Save image URL
            created_by=request.user if getattr(request, "user", None) and request.user.is_authenticated else None,
        )

        return Response({
            "message": "Product added successfully!",
            "product": {
                "id": product.id,
                "name": product.name,
                "price": float(product.price),
                "description": product.description,
                "category": product.category,
                "stock": product.stock,
                "image": product.image,
            }
        }, status=status.HTTP_201_CREATED)



class EditProductView(APIView):
    def patch(self, request):
        product_id = request.data.get('id')
        if not product_id:
            return Response({"error": "id is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            product = Product.objects.get(id=int(product_id))
        except (Product.DoesNotExist, ValueError, TypeError):
            return Response({"error": "Product not found."}, status=status.HTTP_404_NOT_FOUND)

        # Optional updates
        for key, attr in [
            ("name", "name"),
            ("description", "description"),
            ("category", "category"),
            ("image", "image"),
        ]:
            val = request.data.get(key)
            if val is not None:
                setattr(product, attr, val)

        if "price" in request.data:
            try:
                product.price = Decimal(str(request.data.get("price")))
                if product.price < 0:
                    raise ValueError
            except (ValueError, TypeError):
                return Response({"error": "Invalid price."}, status=status.HTTP_400_BAD_REQUEST)

        if "stock" in request.data:
            try:
                product.stock = int(request.data.get("stock"))
                if product.stock < 0:
                    raise ValueError
            except (ValueError, TypeError):
                return Response({"error": "Invalid stock."}, status=status.HTTP_400_BAD_REQUEST)

        product.save()
        return Response({
            "message": "Product edited successfully!",
            "product": {
                "id": product.id,
                "name": product.name,
                "price": float(product.price),
                "description": product.description,
                "category": product.category,
                "stock": product.stock
            }
        }, status=status.HTTP_200_OK)


class DeleteProductView(APIView):
    def delete(self, request):
        product_id = request.data.get('id')
        if not product_id:
            return Response({"error": "id is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            product = Product.objects.get(id=int(product_id))
        except (Product.DoesNotExist, ValueError, TypeError):
            return Response({"error": "Product not found."}, status=status.HTTP_404_NOT_FOUND)
        product.delete()
        return Response({"message": "Product deleted successfully!"}, status=status.HTTP_200_OK)


class ViewAllProducts(APIView):
    def get(self, request):
        products = Product.objects.all().order_by("-created_at")
        product_list = [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "price": float(p.price),
                "stock": p.stock,
                "category": p.category,
                "image": p.image or "",  # ✅ Include image field
            }
            for p in products
        ]
        return Response({"products": product_list}, status=status.HTTP_200_OK)




class ProductSearchView(APIView):
    def get(self, request):
        query = request.query_params.get('query', '')
        products = Product.objects.filter(name__icontains=query).order_by("-created_at")
        data = [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "price": float(p.price),
                "category": p.category,
                "stock": p.stock,
                "image": getattr(p, "image", ""),
            }
            for p in products
        ]
        return Response({"products": data}, status=status.HTTP_200_OK)
    
class ProductListView(View):
    def get(self, request):
        products = Product.objects.all().order_by("-created_at")
        return render(request, "e-com/product_list.html", {"products": products})    
  

# ─────────────────────────────
# Cart
# ─────────────────────────────

class Addproducttocartview(APIView):
    def post(self, request):
        email = request.data.get('email')
        product_id = request.data.get('product_id')
        quantity = request.data.get('quantity', 1)

        if not all([email, product_id]):
            return Response({"error": "Email and Product ID are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        try:
            product = Product.objects.get(id=int(product_id))
        except (Product.DoesNotExist, ValueError, TypeError):
            return Response({"error": "Product not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            qty = int(quantity)
            if qty < 1: raise ValueError
        except (ValueError, TypeError):
            return Response({"error": "Invalid quantity."}, status=status.HTTP_400_BAD_REQUEST)

        item, created = Cart.objects.get_or_create(user=user, product=product, defaults={"quantity": qty})
        if not created:
            item.quantity += qty
            item.save()

        return Response({"message": "Product added to cart.", "quantity": item.quantity}, status=status.HTTP_200_OK)


class ViewCartView(APIView):
    def get(self, request):
        email = request.query_params.get('email')
        if not email:
            return Response({"error": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        cart_items = Cart.objects.select_related("product").filter(user=user)
        data = [{
            "product_id": ci.product.id,
            "item_name": ci.product.name,
            "item_price": float(ci.product.price),
            "quantity": ci.quantity,
            "subtotal": float(ci.product.price * ci.quantity)
        } for ci in cart_items]
        total = sum(ci.product.price * ci.quantity for ci in cart_items)
        return Response({"cart_items": data, "total_amount": float(total)}, status=status.HTTP_200_OK)
    
class Editcartview(APIView):
    def patch(self, request):
        email = request.data.get('email')
        product_id = request.data.get('product_id')
        quantity = request.data.get('quantity')

        if not all([email, product_id, quantity]):
            return Response({"error": "Email, Product ID, and Quantity are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        try:
            product = Product.objects.get(id=int(product_id))
        except (Product.DoesNotExist, ValueError, TypeError):
            return Response({"error": "Product not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            qty = int(quantity)
            if qty < 1: raise ValueError
        except (ValueError, TypeError):
            return Response({"error": "Invalid quantity."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            item = Cart.objects.get(user=user, product=product)
        except Cart.DoesNotExist:
            return Response({"error": "Product not in cart."}, status=status.HTTP_404_NOT_FOUND)

        item.quantity = qty
        item.save()
        return Response({"message": "Cart updated successfully.", "quantity": item.quantity}, status=status.HTTP_200_OK)


class Deleteitemincartview(APIView):
    def delete(self, request):
        email = request.data.get('email')
        product_id = request.data.get('product_id')

        if not all([email, product_id]):
            return Response({"error": "Email and Product ID are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        try:
            product = Product.objects.get(id=int(product_id))
        except (Product.DoesNotExist, ValueError, TypeError):
            return Response({"error": "Product not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            item = Cart.objects.get(user=user, product=product)
        except Cart.DoesNotExist:
            return Response({"error": "Product not in cart."}, status=status.HTTP_404_NOT_FOUND)

        item.delete()
        return Response({"message": "Product removed from cart successfully.", "product": product.name},
                        status=status.HTTP_200_OK)

# ─────────────────────────────
# Orders & Payments (mock)
# ─────────────────────────────

class PlaceOrderView(APIView):
    def post(self, request):
        email = request.data.get('email')
        address_id = request.data.get('address_id')  # optional – attach saved address

        if not email:
            return Response({"error": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        cart_items = list(Cart.objects.select_related("product").filter(user=user))
        if not cart_items:
            return Response({"error": "Cart is empty."}, status=status.HTTP_400_BAD_REQUEST)

        # compute total, check stock
        total = Decimal("0.00")
        for ci in cart_items:
            if ci.quantity > ci.product.stock:
                return Response(
                    {"error": f"Insufficient stock for {ci.product.name}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            total += ci.product.price * ci.quantity

        shipping_addr = None
        if address_id:
            try:
                shipping_addr = Address.objects.get(id=int(address_id), user=user)
            except (Address.DoesNotExist, ValueError, TypeError):
                return Response({"error": "Address not found."}, status=status.HTTP_404_NOT_FOUND)

        order = Order.objects.create(user=user, total_amount=total, status="Pending", shipping_address=shipping_addr)

        for ci in cart_items:
            OrderItem.objects.create(
                order=order,
                product=ci.product,
                quantity=ci.quantity,
                price_at_purchase=ci.product.price,
            )
            # reduce stock
            ci.product.stock -= ci.quantity
            ci.product.save()

        # clear cart
        Cart.objects.filter(user=user).delete()

        return Response({"message": "Order placed successfully.", "order_id": order.id,
                         "total_amount": float(order.total_amount)}, status=status.HTTP_200_OK)


class Orderlistview(APIView):
    def get(self, request):
        orders = Order.objects.select_related("user").all().order_by("-id")
        order_data = [{
            "order_id": o.id,
            "user": o.user.username,
            "total_amount": float(o.total_amount),
            "status": o.status,
            "created_at": o.created_at,
        } for o in orders]
        return Response({"orders": order_data}, status=status.HTTP_200_OK)


class Orderdetailview(APIView):
    def get(self, request, order_id):
        try:
            order = Order.objects.get(id=int(order_id))
        except (Order.DoesNotExist, ValueError, TypeError):
            return Response({"error": "Order not found."}, status=status.HTTP_404_NOT_FOUND)

        items = order.items.select_related("product").all()
        items_data = [{
            "product_name": it.product.name,
            "quantity": it.quantity,
            "price": float(it.price_at_purchase),
            "subtotal": float(it.subtotal),
        } for it in items]

        addr = order.shipping_address
        address_data = None
        if addr:
            address_data = {
                "street": addr.street, "city": addr.city, "state": addr.state, "zip_code": addr.zip_code
            }

        order_data = {
            "order_id": order.id,
            "user": order.user.username,
            "total_amount": float(order.total_amount),
            "status": order.status,
            "created_at": order.created_at,
            "shipping_address": address_data,
            "items": items_data,
        }
        return Response({"order": order_data}, status=status.HTTP_200_OK)


class Paymentinitiateview(APIView):
    def post(self, request):
        order_id = request.data.get('order_id')
        if not order_id:
            return Response({"error": "Order ID is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            order = Order.objects.get(id=int(order_id))
        except (Order.DoesNotExist, ValueError, TypeError):
            return Response({"error": "Order not found."}, status=status.HTTP_404_NOT_FOUND)
        # integrate real gateway here
        return Response({"message": "Payment initiated successfully.",
                         "order_id": order.id, "amount": float(order.total_amount)}, status=status.HTTP_200_OK)


class Paymentconfirmview(APIView):
    def post(self, request):
        order_id = request.data.get('order_id')
        payment_status = request.data.get('payment_status')
        if not all([order_id, payment_status]):
            return Response({"error": "Order ID and Payment Status are required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            order = Order.objects.get(id=int(order_id))
        except (Order.DoesNotExist, ValueError, TypeError):
            return Response({"error": "Order not found."}, status=status.HTTP_404_NOT_FOUND)

        if payment_status == "success":
            order.status = "Paid"
            order.save()
            return Response({"message": "Payment confirmed successfully."}, status=status.HTTP_200_OK)
        return Response({"error": "Payment failed."}, status=status.HTTP_400_BAD_REQUEST)


class paymentstatusview(APIView):
    def get(self, request, order_id):
        try:
            order = Order.objects.get(id=int(order_id))
        except (Order.DoesNotExist, ValueError, TypeError):
            return Response({"error": "Order not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response({"order_id": order.id, "status": order.status,
                         "total_amount": float(order.total_amount)}, status=status.HTTP_200_OK)

# ─────────────────────────────
# Addresses (user address book)
# ─────────────────────────────

class AddressCreateView(APIView):
    def post(self, request):
        user_id = request.data.get('user_id')
        street = request.data.get('street')
        city = request.data.get('city')
        state = request.data.get('state')
        zip_code = request.data.get('zip_code')

        if not all([user_id, street, city, state, zip_code]):
            return Response({"error": "All fields are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(id=int(user_id))
        except (User.DoesNotExist, ValueError, TypeError):
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        address = Address.objects.create(
            user=user, street=street, city=city, state=state, zip_code=zip_code
        )
        return Response({
            "message": "Address created successfully.",
            "address_id": address.id,
            "street": address.street, "city": address.city, "state": address.state, "zip_code": address.zip_code
        }, status=status.HTTP_201_CREATED)


class AddressUpdateView(APIView):
    def patch(self, request):
        address_id = request.data.get('address_id')
        if not address_id:
            return Response({"error": "Address ID is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            address = Address.objects.get(id=int(address_id))
        except (Address.DoesNotExist, ValueError, TypeError):
            return Response({"error": "Address not found."}, status=status.HTTP_404_NOT_FOUND)

        for f in ["street", "city", "state", "zip_code"]:
            val = request.data.get(f)
            if val:
                setattr(address, f, val)
        address.save()
        return Response({
            "message": "Address updated successfully.",
            "address_id": address.id,
            "street": address.street, "city": address.city, "state": address.state, "zip_code": address.zip_code
        }, status=status.HTTP_200_OK)


class AddressDeleteView(APIView):
    def delete(self, request):
        address_id = request.data.get('address_id')
        if not address_id:
            return Response({"error": "Address ID is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            address = Address.objects.get(id=int(address_id))
        except (Address.DoesNotExist, ValueError, TypeError):
            return Response({"error": "Address not found."}, status=status.HTTP_404_NOT_FOUND)
        address.delete()
        return Response({"message": "Address deleted successfully."}, status=status.HTTP_200_OK)


class AddressListView(APIView):
    def get(self, request):
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response({"error": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(id=int(user_id))
        except (User.DoesNotExist, ValueError, TypeError):
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        addresses = Address.objects.filter(user=user)
        data = [{
            "address_id": a.id,
            "street": a.street, "city": a.city, "state": a.state, "zip_code": a.zip_code
        } for a in addresses]
        return Response({"addresses": data}, status=status.HTTP_200_OK)

# ─────────────────────────────
# Coupons (demo)
# ─────────────────────────────

class CouponApplyView(APIView):
    def post(self, request):
        product_id = request.data.get('product_id')
        coupon_code = request.data.get('coupon_code')
        if not all([product_id, coupon_code]):
            return Response({"error": "Product ID and Coupon Code are required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            product = Product.objects.get(id=int(product_id))
        except (Product.DoesNotExist, ValueError, TypeError):
            return Response({"error": "Product not found."}, status=status.HTTP_404_NOT_FOUND)

        discount_percentage = 10  # demo only
        discounted_price = product.price * Decimal(1 - discount_percentage / 100)
        return Response({
            "message": "Coupon applied successfully.",
            "product_id": product.id,
            "original_price": float(product.price),
            "discounted_price": float(discounted_price)
        }, status=status.HTTP_200_OK)


class CouponRemoveView(APIView):
    def post(self, request):
        product_id = request.data.get('product_id')
        if not product_id:
            return Response({"error": "Product ID is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            product = Product.objects.get(id=int(product_id))
        except (Product.DoesNotExist, ValueError, TypeError):
            return Response({"error": "Product not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response({
            "message": "Coupon removed successfully.",
            "product_id": product.id,
            "original_price": float(product.price)
        }, status=status.HTTP_200_OK)

# ─────────────────────────────
# Notifications
# ─────────────────────────────

class NotificationListView(APIView):
    def get(self, request):
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response({"error": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(id=int(user_id))
        except (User.DoesNotExist, ValueError, TypeError):
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        notifications = Notification.objects.filter(user=user).order_by('-created_at')
        data = [{
            "notification_id": n.id,
            "message": n.message,
            "is_read": n.is_read,
            "created_at": n.created_at,
        } for n in notifications]
        return Response({"notifications": data}, status=status.HTTP_200_OK)
    


# ─────────────────────────────
# UI Template Views (for /ui/... routes)
# ─────────────────────────────
class HomeView(TemplateView):
    template_name = "e-com/home.html"


class RegisterPageView(TemplateView):
    template_name = "e-com/register.html"

class LoginPageView(TemplateView):
    template_name = "e-com/login.html"

class AddProductPageView(TemplateView):
    template_name = "e-com/add_product.html"

class ProductListPageView(TemplateView):
    template_name = "e-com/product_list.html"

class CartPageView(TemplateView):
    template_name = "e-com/cart.html"

class OrdersPageView(TemplateView):
    template_name = "e-com/orders.html"

class OrderDetailPageView(TemplateView):
    template_name = "e-com/order_detail.html"

class ForgetPasswordPageView(TemplateView):
    template_name = "e-com/forget_password.html"

class ResetPasswordPageView(TemplateView):
    template_name = "e-com/reset_password.html"

class VerifyOTPPageView(TemplateView):
    template_name = "e-com/verify_otp.html"

