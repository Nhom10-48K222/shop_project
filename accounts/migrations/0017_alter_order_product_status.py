# Generated by Django 5.0.6 on 2024-12-12 16:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0016_order_product_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='product_status',
            field=models.CharField(choices=[('confirmed', 'Confirmed'), ('shipped', 'Shipped'), ('delivered', 'Delivered'), ('received', 'Received')], default='delivered', max_length=100),
        ),
    ]