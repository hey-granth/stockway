# Generated migration for ShopkeeperProfile field updates

from django.db import migrations, models
import django.contrib.gis.db.models.fields
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0009_shopkeeperprofile_location'),
    ]

    operations = [
        # Update shop_name to add default value
        migrations.AlterField(
            model_name='shopkeeperprofile',
            name='shop_name',
            field=models.CharField(default='', max_length=255),
        ),
        # Update gst_number to add default value (field already exists)
        migrations.AlterField(
            model_name='shopkeeperprofile',
            name='gst_number',
            field=models.CharField(blank=True, default='', max_length=15),
        ),
        # Rename onboarding_completed to is_verified
        migrations.RenameField(
            model_name='shopkeeperprofile',
            old_name='onboarding_completed',
            new_name='is_verified',
        ),
    ]

