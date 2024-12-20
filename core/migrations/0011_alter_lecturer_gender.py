# Generated by Django 5.1 on 2024-12-19 09:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_lecturer_gender'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lecturer',
            name='gender',
            field=models.CharField(choices=[('Male', 'Male'), ('Female', 'Female')], help_text='Gender of the lecturer: Male or Female', max_length=255),
        ),
    ]
