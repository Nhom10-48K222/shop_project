# Generated by Django 5.0.6 on 2024-12-12 15:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0015_orderitem_product_price_alter_orderitem_order'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='product_status',
            field=models.CharField(default=1, max_length=100),
            preserve_default=False,
        ),
    ]
