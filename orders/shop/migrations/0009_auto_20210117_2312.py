# Generated by Django 3.1.1 on 2021-01-17 18:12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0008_auto_20210117_2311'),
    ]

    operations = [
        migrations.RenameField(
            model_name='shop',
            old_name='filename1',
            new_name='filename',
        ),
    ]