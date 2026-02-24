from alembic import op

revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
    CREATE TABLE IF NOT EXISTS targets (
        id UUID PRIMARY KEY,
        name TEXT NOT NULL
            CHECK (length(trim(name)) > 0)
            UNIQUE,
        type TEXT NOT NULL CHECK (type IN ('icmp', 'http')),
        host TEXT NULL,
        url TEXT NULL,
        interval_seconds INT NOT NULL,
        timeout_ms INT NOT NULL,
        enabled BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CHECK (
          (type = 'icmp' AND host IS NOT NULL AND url IS NULL)
          OR
          (type = 'http' AND url IS NOT NULL AND host IS NULL)
        )
    );
""")

    op.execute("""
        CREATE TABLE IF NOT EXISTS probe_results (
            id BIGSERIAL PRIMARY KEY,
            target_id UUID NOT NULL REFERENCES targets(id),
            ts TIMESTAMPTZ NOT NULL,
            success BOOLEAN NOT NULL,
            latency_ms INT NULL,
            status_code INT NULL,
            error TEXT NULL
        );
        """)

    # Supports ORDER BY ts DESC, id DESC for global latest queries and keyset pagination.
    # Includes id to provide deterministic ordering when timestamps collide.
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_probe_results_ts_id_desc
        ON probe_results (ts DESC, id DESC);
        """)

    # Supports per-target queries: latest result (LATERAL top-1) and history ordered by ts DESC.
    # Composite ordering avoids sort and enables efficient keyset pagination.
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_probe_results_target_ts_id_desc
        ON probe_results (target_id, ts DESC, id DESC);
        """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS probe_results;")
    op.execute("DROP TABLE IF EXISTS targets;")
