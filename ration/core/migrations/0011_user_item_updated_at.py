# Generated by Django 2.0.2 on 2018-05-11 04:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_item_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='user_item',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
