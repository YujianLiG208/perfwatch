from __future__ import annotations


def estimate_process_power_score(cpu_percent: float, rss_bytes: int, vram_bytes: int = 0) -> float:
    cpu_component = max(cpu_percent, 0.0) / 100.0
    memory_component = max(rss_bytes, 0) / 1_073_741_824
    vram_component = max(vram_bytes, 0) / 1_073_741_824
    return round(cpu_component * 0.7 + memory_component * 0.05 + vram_component * 0.1, 6)
