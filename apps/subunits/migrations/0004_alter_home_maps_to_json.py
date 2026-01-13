from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('subunits', '0003_alter_subunit_filter_home_map_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                -- Drop defaults first
                ALTER TABLE subunits
                ALTER COLUMN view_home_map DROP DEFAULT,
                ALTER COLUMN filter_home_map DROP DEFAULT;

                -- Convert BOOLEAN → JSONB safely
                ALTER TABLE subunits
                ALTER COLUMN view_home_map TYPE jsonb
                    USING '{}'::jsonb,
                ALTER COLUMN filter_home_map TYPE jsonb
                    USING '{}'::jsonb;
            """,
            reverse_sql="""
                ALTER TABLE subunits
                ALTER COLUMN view_home_map TYPE boolean
                    USING false,
                ALTER COLUMN filter_home_map TYPE boolean
                    USING false;
            """
        )
    ]
