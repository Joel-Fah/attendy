# Generated by Django 5.1 on 2024-10-14 12:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_alter_student_student_number_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='course',
            name='code',
            field=models.CharField(help_text='Course code', max_length=7),
        ),
        migrations.AlterUniqueTogether(
            name='course',
            unique_together={('class_level', 'code')},
        ),
    ]