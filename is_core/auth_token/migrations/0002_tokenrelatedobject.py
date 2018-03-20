from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0001_initial'),
        ('auth_token', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TokenRelatedObject',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.TextField()),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType',
                                           on_delete=models.CASCADE)),
                ('token', models.ForeignKey(related_name='related_objects', to='auth_token.Token',
                                           on_delete=models.CASCADE)),
            ],
        ),
    ]
