# Generated manually to add 'coef' to Matiere
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('matieres', '0003_auto_20260708_1741'),
    ]

    operations = [
        migrations.AddField(
            model_name='matiere',
            name='coef',
            field=models.IntegerField(default=1),
            preserve_default=False,
        ),
    ]
