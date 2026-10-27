CREATE TABLE IF NOT EXISTS projects (
    id CHAR(32) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    technology VARCHAR(200) NOT NULL,
    source VARCHAR(500) NOT NULL,
    sample_code VARCHAR(100) NOT NULL,
    ai_tool VARCHAR(100) NOT NULL,
    ai_model VARCHAR(100) NOT NULL,
    development_date CHAR(10),
    development_notes TEXT NOT NULL,
    created_at VARCHAR(40) NOT NULL,
    updated_at VARCHAR(40) NOT NULL,
    deleting TINYINT NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS scans (
    id CHAR(32) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY,
    project_id CHAR(32) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    filename VARCHAR(200) NOT NULL,
    sha256 CHAR(64) CHARACTER SET ascii NOT NULL,
    size BIGINT UNSIGNED NOT NULL,
    status VARCHAR(20) NOT NULL,
    created_at VARCHAR(40) NOT NULL,
    started_at VARCHAR(40),
    finished_at VARCHAR(40),
    heartbeat_at VARCHAR(40),
    error TEXT,
    coverage JSON NOT NULL,
    methods JSON NOT NULL,
    INDEX scan_project (project_id, created_at),
    INDEX scan_queue (status, created_at),
    CONSTRAINT scan_project_fk FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS findings (
    id CHAR(32) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY,
    scan_id CHAR(32) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    method VARCHAR(10) NOT NULL,
    source_id VARCHAR(512) NOT NULL,
    title TEXT NOT NULL,
    severity VARCHAR(20) NOT NULL,
    path TEXT NOT NULL,
    detail JSON NOT NULL,
    review_status VARCHAR(20) NOT NULL DEFAULT 'unreviewed',
    review_reason TEXT NOT NULL,
    likelihood TINYINT,
    impact TINYINT,
    risk_reason TEXT NOT NULL,
    reviewed_at VARCHAR(40),
    INDEX finding_scan (scan_id),
    CONSTRAINT finding_scan_fk FOREIGN KEY (scan_id) REFERENCES scans(id) ON DELETE CASCADE,
    CHECK (likelihood IS NULL OR likelihood BETWEEN 1 AND 3),
    CHECK (impact IS NULL OR impact BETWEEN 1 AND 3)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
