from rest_framework import serializers

from shop.models import Category, Shop


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name',)
        read_only_fields = ('id',)

class ShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = ('name', 'url', 'state',)
        read_only_fields = ('id',)
