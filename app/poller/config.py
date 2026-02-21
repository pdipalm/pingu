from dataclasses import dataclass
import yaml

@dataclass(frozen=True)
class TargetCfg:
    name: str
    type: str  # "icmp" or "http"
    host: str | None
    url: str | None
    interval_seconds: int
    timeout_ms: int
    enabled: bool


def load_targets(path: str) -> list[TargetCfg]:
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    items = raw.get("targets", [])
    out: list[TargetCfg] = []
    for it in items:
        out.append(
            TargetCfg(
                name=str(it["name"]),
                type=str(it["type"]),
                host=it.get("host"),
                url=it.get("url"),
                interval_seconds=int(it["interval_seconds"]),
                timeout_ms=int(it["timeout_ms"]),
                enabled=bool(it.get("enabled", True)),
            )
        )
    return out