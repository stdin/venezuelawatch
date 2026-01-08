from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            # Create TimescaleDB hypertable (requires TimescaleDB extension)
            sql="""
                -- Enable TimescaleDB extension (must be done by superuser in Cloud SQL)
                -- CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

                -- Convert events table to hypertable partitioned by timestamp
                -- Chunk interval: 7 days (good for event data)
                SELECT create_hypertable('events', 'timestamp',
                    chunk_time_interval => INTERVAL '7 days',
                    if_not_exists => TRUE
                );

                -- Create compression policy (compress data older than 7 days)
                SELECT add_compression_policy('events', INTERVAL '7 days');

                -- Create retention policy (drop data older than 6 months for now)
                SELECT add_retention_policy('events', INTERVAL '6 months');
            """,
            reverse_sql="""
                SELECT remove_retention_policy('events');
                SELECT remove_compression_policy('events');
                -- Note: Cannot easily reverse create_hypertable
            """
        ),
    ]
