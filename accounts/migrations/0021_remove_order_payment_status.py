# Generated by Django 5.0.6 on 2024-12-14 13:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0020_alter_order_payment_status'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='order',
            name='payment_status',
        ),
    ]
