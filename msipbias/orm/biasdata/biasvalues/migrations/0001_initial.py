# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Temperature',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('temperature', models.FloatField(help_text=b'temperature in K')),
                ('create_time', models.DateTimeField(help_text=b'When temperature was measured', auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='TemperatureChannel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('channel', models.IntegerField(help_text=b'Channel Number')),
                ('description', models.CharField(help_text=b'Description of where the temperature sensor is', max_length=100, null=True, blank=True)),
                ('polarization', models.IntegerField(help_text=b'Polarization (one of 0 or 1)')),
                ('sensor', models.IntegerField(help_text=b'sensor number within the polarization')),
            ],
        ),
        migrations.AddField(
            model_name='temperature',
            name='tempchannel',
            field=models.ForeignKey(to='biasvalues.TemperatureChannel'),
        ),
    ]
