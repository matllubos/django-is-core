from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth_token', '0003_usertokentakeover'),
    ]

    operations = [
        migrations.AddField(
            model_name='token',
            name='backend',
            field=models.CharField(default='django.contrib.auth.backends.ModelBackend', max_length=255),
            preserve_default=False,
        ),
    ]
