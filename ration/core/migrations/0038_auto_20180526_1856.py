# Generated by Django 2.0.2 on 2018-05-27 01:56

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0037_auto_20180526_1844'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='log',
            name='taglist',
        ),
        migrations.DeleteModel(
            name='Log',
        ),
    ]
