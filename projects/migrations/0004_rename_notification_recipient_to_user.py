from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("projects", "0003_alter_chapter_status"),
    ]

    operations = [
        migrations.RenameField(
            model_name="notification",
            old_name="recipient",
            new_name="user",
        ),
    ]

