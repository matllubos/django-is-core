# Generated by Django 3.2 on 2022-12-06 12:51

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('issue_tracker', '0002_auto_20210401_1128'),
    ]

    operations = [
        migrations.AddField(
            model_name='issue',
            name='parent',
            field=models.ForeignKey(
                blank=True,
                null=True, on_delete=django.db.models.deletion.CASCADE,
                related_name='subissues',
                to='issue_tracker.issue',
                verbose_name='Parent'
            ),
        ),
    ]