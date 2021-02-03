from django.urls import path

from shop.views import CategoryView, ShopView, PartnerUpdate, LoginAccount, RegisterAccount, ProductListView, \
    ProductView, BasketView, OrderView

# import orders.shop

# from django.views import reset_password_request_token, reset_password_confirm

# from shop.views import CategoryView

app_name = 'shop'
urlpatterns = [
    path('partner/update', PartnerUpdate.as_view(), name='partner-update'),
    # path('partner/state', PartnerState.as_view(), name='partner-state'),
    # path('partner/orders', PartnerOrders.as_view(), name='partner-orders'),
    path('user/register', RegisterAccount.as_view(), name='user-register'),
    # path('user/register/confirm', ConfirmAccount.as_view(), name='user-register-confirm'),
    # path('user/details', AccountDetails.as_view(), name='user-details'),
    # path('user/contact', ContactView.as_view(), name='user-contact'),
    path('user/login', LoginAccount.as_view(), name='user-login'),
    # path('user/password_reset', reset_password_request_token, name='password-reset'),
    # path('user/password_reset/confirm', reset_password_confirm, name='password-reset-confirm'),
    path('categories', CategoryView.as_view(), name='categories'),
    path('shops', ShopView.as_view(), name='shops'),
    path('products', ProductListView.as_view(), name='products'),
    path('product', ProductView.as_view(), name='product'),
    path('basket', BasketView.as_view(), name='basket'),
    path('order', OrderView.as_view(), name='order'),
]
