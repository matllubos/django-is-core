# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Token',
            fields=[
                ('key', models.CharField(primary_key=True, serialize=False, max_length=40)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('last_access', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                ('user_agent', models.CharField(blank=True, null=True, max_length=256)),
                ('expiration', models.BooleanField(default=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, related_name='auth_token')),
            ],
        ),
    ]
