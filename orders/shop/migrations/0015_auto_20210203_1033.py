# Generated by Django 3.0.8 on 2021-02-03 05:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0014_auto_20210203_1028'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='orderitem',
            name='unique_order_item',
        ),
        migrations.AddConstraint(
            model_name='orderitem',
            constraint=models.UniqueConstraint(fields=('order_id', 'product_info_id'), name='unique_order_item'),
        ),
    ]