# Generated by Django 5.0.6 on 2024-12-14 14:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0021_remove_order_payment_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='payment_status',
            field=models.CharField(default='Pending', max_length=255),
        ),
        migrations.AddField(
            model_name='order',
            name='product_status',
            field=models.CharField(max_length=50, null=True),
        ),
    ]
