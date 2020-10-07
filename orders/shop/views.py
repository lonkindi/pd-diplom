# Create your views here.
from rest_framework.generics import ListAPIView

from orders.shop.models import Category
from orders.shop.serializers import CategorySerializer


class CategoryView(ListAPIView):
    """
    Класс для просмотра категорий
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
