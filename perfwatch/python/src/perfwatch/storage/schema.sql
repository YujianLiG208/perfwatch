CREATE TABLE IF NOT EXISTS samples_system (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts_ms INTEGER NOT NULL,
    cpu_usage_percent REAL,
    cpu_frequency_mhz REAL,
    cpu_package_power_watts REAL,
    cpu_temperature_celsius REAL,
    memory_total_bytes INTEGER,
    memory_used_bytes INTEGER,
    battery_available INTEGER,
    battery_charging INTEGER,
    battery_percent REAL,
    battery_power_watts REAL,
    battery_energy_remaining_wh REAL,
    gpu_available INTEGER,
    gpu_vendor TEXT,
    gpu_usage_percent REAL,
    gpu_vram_total_bytes INTEGER,
    gpu_vram_used_bytes INTEGER,
    gpu_power_watts REAL,
    gpu_temperature_celsius REAL
);

CREATE TABLE IF NOT EXISTS samples_process (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts_ms INTEGER NOT NULL,
    pid INTEGER,
    name TEXT,
    cpu_percent REAL,
    rss_bytes INTEGER,
    vram_bytes INTEGER,
    estimated_power_score REAL
);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts_ms INTEGER NOT NULL,
    level TEXT NOT NULL,
    source TEXT NOT NULL,
    message TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_samples_system_ts_ms ON samples_system (ts_ms);
CREATE INDEX IF NOT EXISTS idx_samples_process_ts_ms ON samples_process (ts_ms);
CREATE INDEX IF NOT EXISTS idx_events_ts_ms ON events (ts_ms);
