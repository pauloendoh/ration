# Generated by Django 2.0.2 on 2018-05-07 05:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_item_tag'),
    ]

    operations = [
        migrations.RenameField(
            model_name='item',
            old_name='created_on',
            new_name='created_at',
        ),
    ]
