# Generated by Django 5.2 on 2025-07-06 00:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_alter_portfolio_image'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='portfolio',
            index=models.Index(fields=['user_id'], name='users_portf_user_id_a447b4_idx'),
        ),
    ]
