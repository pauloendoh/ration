# Generated by Django 2.0.2 on 2018-05-18 17:21

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0027_auto_20180518_1001'),
    ]

    operations = [
        migrations.AddField(
            model_name='update',
            name='interaction',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='updates', to='core.User_Item'),
        ),
    ]
