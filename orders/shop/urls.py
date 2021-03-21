from django.urls import path
from rest_framework.routers import DefaultRouter, SimpleRouter

from shop.views import CategoryView, ShopView, PartnerUpdate, LoginAccount, RegisterAccount, ProductListView, \
    ProductView, BasketView, OrderView, PartnerOrders

app_name = 'shop'
router = DefaultRouter()
router.register(r'partner/orders', PartnerOrders, basename='MyUser')
urlpatterns = router.urls
urlpatterns += [
    path('partner/update', PartnerUpdate.as_view(), name='partner-update'),
    # path('partner/orders', PartnerOrders.as_view({'get': 'get'}), name='partner-orders'),
    path('user/register', RegisterAccount.as_view(), name='user-register'),
    path('user/login', LoginAccount.as_view(), name='user-login'),
    path('categories', CategoryView.as_view(), name='categories'),
    path('shops', ShopView.as_view(), name='shops'),
    path('products', ProductListView.as_view(), name='products'),
    path('product', ProductView.as_view(), name='product'),
    path('basket', BasketView.as_view(), name='basket'),
    path('order', OrderView.as_view(), name='order'),
]


