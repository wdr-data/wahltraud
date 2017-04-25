# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-04-25 10:33
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0004_facebookuser'),
    ]

    operations = [
        migrations.AlterField(
            model_name='entry',
            name='link_one',
            field=models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='backend.Entry', verbose_name='Link 1'),
        ),
    ]
