# Generated by Django 5.0.7 on 2024-08-19 02:45

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_user_email_token_user_token_created_at_and_more'),
    ]

    operations = [
        migrations.DeleteModel(
            name='PasswordResetToken',
        ),
    ]
