from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='customuser',
            options={'verbose_name': 'User', 'verbose_name_plural': 'Users'},
        ),
        migrations.RemoveField(
            model_name='customuser',
            name='failed_login_attempts',
        ),
        migrations.RemoveField(
            model_name='customuser',
            name='last_failed_login_attempt',
        ),
        migrations.RemoveField(
            model_name='customuser',
            name='login_limit',
        ),
        migrations.RemoveField(
            model_name='customuser',
            name='profile_picture',
        ),
        migrations.DeleteModel(
            name='ActivationCode',
        ),
        migrations.AlterField(
            model_name='customuser',
            name='email',
            field=models.EmailField(max_length=254, unique=True),
        ),
    ]
