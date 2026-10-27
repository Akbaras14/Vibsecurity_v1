CREATE TABLE project_versions (
 id CHAR(32) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY,
 project_id CHAR(32) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 sha256 CHAR(64) CHARACTER SET ascii NOT NULL,
 documentation JSON NOT NULL,
 created_at VARCHAR(40) NOT NULL,
 UNIQUE KEY version_hash(project_id,sha256),
 FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
INSERT INTO project_versions(id,project_id,sha256,documentation,created_at)
 SELECT MIN(id),project_id,sha256,JSON_OBJECT('legacy',true),MIN(created_at) FROM scans GROUP BY project_id,sha256;
ALTER TABLE scans ADD version_id CHAR(32) CHARACTER SET ascii COLLATE ascii_bin NULL;
UPDATE scans s JOIN project_versions v ON v.project_id=s.project_id AND v.sha256=s.sha256 SET s.version_id=v.id;
ALTER TABLE scans ADD FOREIGN KEY(version_id) REFERENCES project_versions(id);
CREATE TABLE research_protocol (
 id INT PRIMARY KEY,
 manifest JSON NOT NULL,
 sha256 CHAR(64) CHARACTER SET ascii NOT NULL,
 created_at VARCHAR(40) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
CREATE TABLE research_samples (
 project_id CHAR(32) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY,
 version_id CHAR(32) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 protocol_id INT NOT NULL,
 FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE,
 FOREIGN KEY(version_id) REFERENCES project_versions(id),
 FOREIGN KEY(protocol_id) REFERENCES research_protocol(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
CREATE TABLE validation_history (
 id CHAR(32) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY,
 finding_id CHAR(32) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 decision JSON NOT NULL,
 created_at VARCHAR(40) NOT NULL,
 INDEX history_finding(finding_id,created_at),
 FOREIGN KEY(finding_id) REFERENCES findings(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
INSERT INTO validation_history(id,finding_id,decision,created_at)
 SELECT REPLACE(UUID(),'-',''),id,JSON_OBJECT('legacy',true,'review_status',review_status,'review_reason',review_reason,'likelihood',likelihood,'impact',impact,'risk_reason',risk_reason),reviewed_at
 FROM findings WHERE reviewed_at IS NOT NULL;
UPDATE findings SET likelihood=NULL,impact=NULL,
 risk_reason=CONCAT('Penilaian lama tersimpan pada riwayat; perlu penilaian ulang R1. ',risk_reason)
 WHERE likelihood IS NOT NULL OR impact IS NOT NULL;
CREATE TABLE risk_scenarios (
 id CHAR(32) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY,
 validation_id CHAR(32) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 position INT NOT NULL,
 rubric VARCHAR(10) NOT NULL,
 scenario TEXT NOT NULL,
 asset TEXT NOT NULL,
 evidence TEXT NOT NULL,
 likelihood TINYINT NULL,
 confidentiality TINYINT NULL,
 integrity TINYINT NULL,
 availability TINYINT NULL,
 reason TEXT NOT NULL,
 uncertainty TEXT NOT NULL,
 FOREIGN KEY(validation_id) REFERENCES validation_history(id) ON DELETE CASCADE,
 CHECK(likelihood IS NULL OR likelihood BETWEEN 1 AND 3),
 CHECK(confidentiality IS NULL OR confidentiality BETWEEN 1 AND 3),
 CHECK(integrity IS NULL OR integrity BETWEEN 1 AND 3),
 CHECK(availability IS NULL OR availability BETWEEN 1 AND 3)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
