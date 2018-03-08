from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('auth_token', '0002_tokenrelatedobject'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserTokenTakeover',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_active', models.BooleanField()),
                ('token', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                            related_name='user_takeovers', to='auth_token.Token')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                           related_name='user_token_takeovers', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
