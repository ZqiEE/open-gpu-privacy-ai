CREATE TABLE IF NOT EXISTS nodes (
    node_id TEXT PRIMARY KEY,
    device_name TEXT NOT NULL,
    cpu_threads INTEGER NOT NULL,
    memory_gb DOUBLE PRECISION NOT NULL,
    has_gpu BOOLEAN NOT NULL,
    gpu_name TEXT,
    contribution_percent INTEGER NOT NULL,
    score INTEGER NOT NULL,
    trust INTEGER NOT NULL DEFAULT 30,
    status TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS jobs (
    job_id TEXT PRIMARY KEY,
    job_type TEXT NOT NULL,
    payload_json JSONB NOT NULL,
    status TEXT NOT NULL DEFAULT 'queued',
    assigned_to TEXT REFERENCES nodes(node_id),
    attempts INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    assigned_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_jobs_status_created ON jobs(status, created_at);
CREATE INDEX IF NOT EXISTS idx_jobs_assigned_to ON jobs(assigned_to);

CREATE TABLE IF NOT EXISTS results (
    result_id TEXT PRIMARY KEY,
    node_id TEXT NOT NULL REFERENCES nodes(node_id),
    job_id TEXT NOT NULL REFERENCES jobs(job_id),
    status TEXT NOT NULL,
    output_summary TEXT NOT NULL,
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS verifications (
    verification_id TEXT PRIMARY KEY,
    result_id TEXT NOT NULL REFERENCES results(result_id),
    job_id TEXT NOT NULL REFERENCES jobs(job_id),
    node_id TEXT NOT NULL REFERENCES nodes(node_id),
    score DOUBLE PRECISION NOT NULL,
    passed BOOLEAN NOT NULL,
    reason TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS model_versions (
    model_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    base_model TEXT NOT NULL,
    source_job_id TEXT NOT NULL,
    notes TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS app_events (
    event_id TEXT PRIMARY KEY,
    level TEXT NOT NULL,
    source TEXT NOT NULL,
    message TEXT NOT NULL,
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
