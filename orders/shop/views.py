# Create your views here.
from rest_framework.generics import ListAPIView

from shop.models import Category
from shop.serializers import CategorySerializer


class CategoryView(ListAPIView):
    """
    Класс для просмотра категорий
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
