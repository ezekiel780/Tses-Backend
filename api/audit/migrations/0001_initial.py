from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event', models.CharField(choices=[('OTP_REQUESTED', 'OTP Requested'), ('OTP_VERIFIED', 'OTP Verified'), ('OTP_FAILED', 'OTP Failed'), ('OTP_LOCKED', 'OTP Locked')], db_index=True, max_length=50)),
                ('email', models.EmailField(db_index=True, max_length=254)),
                ('ip_address', models.GenericIPAddressField()),
                ('user_agent', models.TextField(blank=True, null=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['email', 'created_at'], name='audit_audit_email_created_idx'),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['event', 'created_at'], name='audit_audit_event_created_idx'),
        ),
    ]
