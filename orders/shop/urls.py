from django.urls import path

from shop import views
# import orders.shop

# from django.views import reset_password_request_token, reset_password_confirm

# from shop.views import CategoryView

app_name = 'shop'
urlpatterns = [
    path('categories', views.CategoryView.as_view(), name='categories'),
]