# Generated by Django 4.0.4 on 2022-04-23 08:42

from django.conf import settings
import django.contrib.auth.models
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='KejaUser',
            fields=[
                ('user_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL)),
                ('created', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated', models.DateTimeField(default=django.utils.timezone.now)),
                ('dob', models.DateField(blank=True, null=True)),
                ('national_id_no', models.IntegerField(blank=True, null=True, unique=True)),
                ('user_type', models.CharField(choices=[('LANDLORD', 'LANDLORD'), ('TENANT', 'TENANT'), ('ADMIN', 'ADMIN')], max_length=20)),
                ('landlord', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='keja_user.kejauser')),
            ],
            options={
                'abstract': False,
            },
            bases=('auth.user', models.Model),
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Contact',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated', models.DateTimeField(default=django.utils.timezone.now)),
                ('contact_type', models.CharField(choices=[('PHONE', 'PHONE'), ('EMAIL', 'EMAIL')], max_length=20)),
                ('contact_value', models.CharField(max_length=256)),
                ('is_active', models.BooleanField(default=False)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_contacts', to='keja_user.kejauser')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
