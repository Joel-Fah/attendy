# Generated by Django 5.1 on 2024-08-27 03:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0021_alter_lecturer_slug_alter_student_slug'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lecturer',
            name='slug',
            field=models.SlugField(help_text='Slug of the lecturer', max_length=255),
        ),
    ]