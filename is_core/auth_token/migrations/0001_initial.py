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
                ('key', models.CharField(max_length=40, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('last_access', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                ('user_agent', models.CharField(max_length=256, null=True, blank=True)),
                ('expiration', models.BooleanField(default=True)),
                ('ip', models.GenericIPAddressField()),
                ('auth_slug', models.SlugField(null=True, blank=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, related_name='auth_token',
                                           on_delete=models.CASCADE)),
            ],
        ),
    ]
