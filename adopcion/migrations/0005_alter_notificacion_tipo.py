# Generated by Django 4.2.23 on 2025-06-26 03:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('adopcion', '0004_update_donation_and_mascota_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notificacion',
            name='tipo',
            field=models.CharField(max_length=50),
        ),
    ]
