# Generated by Django 2.2.11 on 2022-09-29 11:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('facility', '0321_merge_20220921_2255'),
    ]

    operations = [
        migrations.AddField(
            model_name='patientconsultation',
            name='review_interval',
            field=models.IntegerField(default=-1),
        ),
    ]
