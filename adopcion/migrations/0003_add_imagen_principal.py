# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('adopcion', '0002_alter_solicitudadopcion_unique_together_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='mascota',
            name='imagen_principal',
            field=models.ImageField(blank=True, help_text='Imagen principal de la mascota', null=True, upload_to='mascotas/'),
        ),
    ] 