# Generated by Django 2.0.2 on 2018-06-02 03:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0041_auto_20180526_1940'),
    ]

    operations = [
        migrations.AlterField(
            model_name='item',
            name='tags',
            field=models.ManyToManyField(blank=True, null=True, related_name='items', to='core.Tag'),
        ),
        migrations.AlterField(
            model_name='tag',
            name='is_official',
            field=models.BooleanField(default=0),
        ),
    ]
