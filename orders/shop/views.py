# Create your views here.
import os

from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.validators import URLValidator
from django.db.models import Q, F, Sum
from django.db import IntegrityError
from django.http import JsonResponse
from django.core.exceptions import ValidationError

from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token

from requests import get

from yaml import load as load_yaml, Loader
from json import loads as load_json

from shop.models import Category, Product, ProductInfo, Parameter, ProductParameter, Shop, Order, OrderItem
from shop.serializers import CategorySerializer, ShopSerializer, MyUserSerializer, ProductInfoSerializer, \
    OrderSerializer, OrderItemSerializer


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
    +Класс для просмотра категорий
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class ShopView(ListAPIView):
    """
    +Класс для просмотра списка магазинов
    """
    queryset = Shop.objects.filter(state=True)
    serializer_class = ShopSerializer


class PartnerUpdate(APIView):
    """
    +Класс для обновления прайса от поставщика
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

class BasketView(APIView):
    """
    Класс для работы с корзиной пользователя
    """

    # получить корзину
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Требуется авторизация!'}, status=403)
        basket = Order.objects.filter(
            user_id=request.user.id, state='basket').prefetch_related(
            'ordered_items__product_info__product__category',
            'ordered_items__product_info__product_parameters__parameter').annotate(
            total_sum=Sum(F('ordered_items__quantity') * F('ordered_items__product_info__price'))).distinct()

        serializer = OrderSerializer(basket, many=True)
        return Response(serializer.data)

    # редактировать корзину
    def put(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Необходима авторизация'}, status=403)

        items_sting = request.data.get('items')
        print('items_sting= ', items_sting)
        if items_sting:
            try:
                items_dict = load_json(items_sting)
                print('items_dict=', items_dict)
            except ValueError:
                JsonResponse({'Status': False, 'Errors': 'Неверный формат запроса'})
            else:
                basket, _ = Order.objects.get_or_create(user_id=request.user.id, state='basket')
                objects_updated = 0
                for order_item in items_dict:
                    order_item.update({'order': basket.id})
                    print('order_item=', order_item)
                    # serializer = OrderItemSerializer(data=order_item)
                    # print('serializer=', serializer)
                    # if serializer.is_valid():
                    #     try:
                    #         serializer.save()
                    #     except IntegrityError as error:
                    #         return JsonResponse({'Status': False, 'Errors serializer.save()': str(error)})
                    #     else:
                    #         objects_updated += 1
                    #
                    # else:
                    objects_updated += OrderItem.objects.filter(order_id=basket.id,
                                                                product_info_id=order_item['product_info'])\
                        .update(quantity=order_item['quantity'])
                        # JsonResponse({'Status': False, 'Errors serializer': serializer.errors})

                return JsonResponse({'Status': True, 'Отредактированно объектов': objects_updated})
        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})

    # удалить товары из корзины
    def delete(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Необходима авторизация'}, status=403)

        items_sting = request.data.get('items')
        if items_sting:
            # print('items_sting=', items_sting)
            items_list = items_sting.split(',')
            # print('items_list', items_list)
            basket, _ = Order.objects.get_or_create(user_id=request.user.id, state='basket')
            query = Q()
            objects_deleted = False
            for order_item_id in items_list:
                #print('order_item_type=', type(order_item_id))
                if order_item_id.isdigit():
                    item_id = int(order_item_id)
                    query = query | Q(order_id=basket.id, product_info_id=item_id)
                    objects_deleted = True

            if objects_deleted:
                # print('OrderItem.objects.filter(query)=', query)
                deleted_count = OrderItem.objects.filter(query).delete()[0]
                return JsonResponse({'Status': True, 'Удалено объектов': deleted_count})
        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})

    # добавить позиции в корзину
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Требуется авторизация!'}, status=403)

        items_sting = request.data.get('items')
        #print('items_sting =', items_sting)
        if items_sting:
            try:
                items_dict = load_json(items_sting)
                #print('items_dict =', items_dict)
            except ValueError:
                JsonResponse({'Status': False, 'Errors': 'Неверный формат запроса'})
            else:
                basket, _ = Order.objects.get_or_create(user_id=request.user.id, state='basket')
                # print('basket=', basket.id)
                objects_inserted = 0
                for order_item in items_dict:
                    if type(order_item['product_info_id']) == int and type(order_item['quantity']) == int \
                            and order_item['quantity'] > 0:
                        product_info = ProductInfo.objects.filter(id=order_item['product_info_id'])
                        if product_info:
                            current_item = OrderItem.objects.filter(order_id=basket.id, product_info_id=product_info[0].id)
                            if not current_item :
                                OrderItem.objects.create(order_id=basket.id,
                                                         product_info_id=order_item['product_info_id'],
                                                         quantity=order_item['quantity'])
                                objects_inserted += 1

                            # print('product_info=', product_info)
                            # print('order_item[quantity]=', order_item['quantity'])
                            # current_item = OrderItem.objects.get_or_create(order_id=basket.id, product_info_id=order_item['product_info_id'], quantity=0) #order_item['quantity'])
                            # print('OrderItem=', OrderItem.objects.filter(order_id=basket.id)) #, product_info_id=order_item['id']))
                            # objects_inserted += 1 OrderItem.objects.filter(order_id=basket.id, product_info__product__id=order_item['id']).update(
                                # quantity=order_item['quantity'])
                    #     return JsonResponse({'Status': False, 'Errors': 'Указанный товар не найден'})
                    # return JsonResponse({'Status': False, 'Errors': 'Не корректный тип аргумента'})
                return JsonResponse({'Status': True, 'Добавлено объектов': objects_inserted})
        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})

class OrderView(APIView):
    """
    Класс для получения и размешения заказов пользователями
    """

    # получить мои заказы
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Требуется авторизация'}, status=403)
        order = Order.objects.filter(
            user_id=request.user.id).exclude(state='basket').prefetch_related(
            'ordered_items__product_info__product__category',
            'ordered_items__product_info__product_parameters__parameter').select_related('contact').annotate(
            total_sum=Sum(F('ordered_items__quantity') * F('ordered_items__product_info__price'))).distinct()

        serializer = OrderSerializer(order, many=True)
        return Response(serializer.data)

    # разместить заказ из корзины
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Требуется авторизация'}, status=403)

        if {'id', 'contact'}.issubset(request.data):
            # print('request.data.id=', request.data['id'].isdigit())
            if request.data['id'].isdigit():
                try:
                    is_updated = Order.objects.filter(
                        user_id=request.user.id, id=request.data['id'], state='basket').update(
                        contact_id=request.data['contact'],
                        state='new')
                except IntegrityError as error:
                    print(error)
                    return JsonResponse({'Status': False, 'Errors': 'Неправильно указаны аргументы'})
                else:
                    if is_updated:
                        # new_order.send(sender=self.__class__, user_id=request.user.id)
                        return JsonResponse({'Status': True, 'Оформлен заказ №': request.data['id']})
        return JsonResponse({'Status': False, 'Errors': 'Корзина не найдена'})