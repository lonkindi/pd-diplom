# Create your views here.
import os

from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.validators import URLValidator
from django.db.models import Q
from django.http import JsonResponse
from django.core.exceptions import ValidationError

from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token

from requests import get

from yaml import load as load_yaml, Loader

from shop.models import Category, Product, ProductInfo, Parameter, ProductParameter, Shop
from shop.serializers import CategorySerializer, ShopSerializer, MyUserSerializer, ProductInfoSerializer


class LoginAccount(APIView):
    """
    Класс для авторизации пользователей
    """

    # Авторизация методом POST
    def post(self, request, *args, **kwargs):

        if {'email', 'password'}.issubset(request.data):
            user = authenticate(request, username=request.data['email'], password=request.data['password'])

            if user is not None:
                if user.is_active:
                    token, _ = Token.objects.get_or_create(user=user)
                    # print('user=', user.email)

                    return JsonResponse({'Status': True, 'Token': token.key})

            return JsonResponse({'Status': False, 'Errors': 'Не удалось авторизовать'})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})


class CategoryView(ListAPIView):
    """
    Класс для просмотра категорий
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class ShopView(ListAPIView):
    """
    Класс для просмотра списка магазинов
    """
    queryset = Shop.objects.filter(state=True)
    serializer_class = ShopSerializer


class PartnerUpdate(APIView):
    """
    Класс для обновления прайса от поставщика
    """

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        if request.user.type != 'shop':
            return JsonResponse({'Status': False, 'Error': 'Только для магазинов'}, status=403)

        shop = Shop.objects.filter(user=request.user)[0]
        price = shop.filename.path

        print('price exists=', os.path.exists(price))

        # validate_url = URLValidator()
        if os.path.exists(price):
        #     validate_url(url)
        # except ValidationError as e:
        #     return JsonResponse({'Status': False, 'Error': str(e)})
        # else:
            # stream = get(url).content
            with open(price, encoding='utf-8') as f:
                data = load_yaml(f, Loader=Loader)
            print('data = ', data)
            # shop, _ = Shop.objects.get_or_create(name=data['shop'], user_id=request.user.id)
            for category in data['categories']:
                # print('category[id]', category['id'], type(category['id']))
                category_object, _ = Category.objects.get_or_create(id=category['id'], name=category['name'])
                category_object.shops.add(shop.id)
                category_object.save()
            ProductInfo.objects.filter(shop_id=shop.id).delete()
            for item in data['goods']:
                product, _ = Product.objects.get_or_create(name=item['name'], category_id=item['category'])

                product_info = ProductInfo.objects.create(product_id=product.id,
                                                          external_id=item['id'],
                                                          model=item['model'],
                                                          price=item['price'],
                                                          price_rrc=item['price_rrc'],
                                                          quantity=item['quantity'],
                                                          shop_id=shop.id)
                for name, value in item['parameters'].items():
                    parameter_object, _ = Parameter.objects.get_or_create(name=name)
                    ProductParameter.objects.create(product_info_id=product_info.id,
                                                    parameter_id=parameter_object.id,
                                                    value=value)

            return JsonResponse({'Status': True})

        return JsonResponse({'Status': False, 'Errors': 'Файл импорта не найден'})


class RegisterAccount(APIView):
    """
    Для регистрации покупателей
    """
    # Регистрация методом POST
    def post(self, request, *args, **kwargs):

        # проверяем обязательные аргументы
        if {'first_name', 'last_name', 'email', 'password', }.issubset(request.data):
            errors = {}

            # проверяем пароль на сложность

            try:
                validate_password(request.data['password'])
            except Exception as password_error:
                error_array = []
                # noinspection PyTypeChecker
                for item in password_error:
                    error_array.append(item)
                return JsonResponse({'Status': False, 'Errors': {'password': error_array}})
            else:
                # проверяем данные для уникальности имени пользователя
                request.data._mutable = True
                request.data.update({})
                user_serializer = MyUserSerializer(data=request.data)
                if user_serializer.is_valid():
                    # сохраняем пользователя
                    user = user_serializer.save()
                    user.set_password(request.data['password'])
                    user.save()
                    # new_user_registered.send(sender=self.__class__, user_id=user.id)
                    return JsonResponse({'Status': True})
                else:
                    return JsonResponse({'Status': False, 'Errors': user_serializer.errors})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})


class ProductListView(APIView):
    """
    Класс для поиска товаров
    """
    def get(self, request, *args, **kwargs):

        query = Q(shop__state=True)
        shop_id = request.query_params.get('shop_id')
        category_id = request.query_params.get('category_id')

        if shop_id:
            query = query & Q(shop_id=shop_id)

        if category_id:
            query = query & Q(product__category_id=category_id)

        # фильтруем и отбрасываем дуликаты
        queryset = ProductInfo.objects.filter(
            query).select_related(
            'shop', 'product__category').prefetch_related(
            'product_parameters__parameter').distinct()

        serializer = ProductInfoSerializer(queryset, many=True)

        return Response(serializer.data)

class ProductView(APIView):
    """
    Класс для выдачи информации о товаре
    """
    def get(self, request, *args, **kwargs):

        # query = Q(shop__state=True)
        product_id = request.query_params.get('id')
        # category_id = request.query_params.get('category_id')

        # if shop_id:
        #     query = query & Q(shop_id=shop_id)
        #
        # if category_id:
        #     query = query & Q(product__category_id=category_id)

        # фильтруем и отбрасываем дуликаты
        queryset = ProductInfo.objects.filter(product__id=
            product_id).prefetch_related(
            'product_parameters__parameter').distinct()

        serializer = ProductInfoSerializer(queryset, many=True)

        return Response(serializer.data)