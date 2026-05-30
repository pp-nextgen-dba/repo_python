from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
import json
from pathlib import Path
import subprocess


@dataclass(frozen=True)
class CpuSample:
    label: str
    cpu_usage: float


@dataclass(frozen=True)
class CpuCollection:
    host: str
    collected_date: str
    command: str
    samples: list[CpuSample]
    max_cpu: float


def parse_sar_cpu_output(output: str) -> list[CpuSample]:
    samples: list[CpuSample] = []

    for line in output.splitlines():
        parts = line.split()
        if len(parts) < 3 or parts[0] == "Average:":
            continue

        cpu_index = next((index for index, part in enumerate(parts) if part == "all"), None)
        if cpu_index is None or cpu_index == len(parts) - 1:
            continue

        try:
            idle = float(parts[-1])
        except ValueError:
            continue

        if not 0 <= idle <= 100:
            continue

        label = " ".join(parts[:cpu_index])
        samples.append(CpuSample(label=label, cpu_usage=round(100 - idle, 2)))

    if not samples:
        raise ValueError("No CPU samples found in sar output")

    return samples


def run_sar_command(interval: int = 2, count: int = 10) -> str:
    command = ["sar", "-u", str(interval), str(count)]
    completed = subprocess.run(command, check=True, capture_output=True, text=True)
    return completed.stdout


def collect_cpu_from_output(
    output: str,
    host: str = "local",
    collected_date: str | None = None,
    command: str = "sar -u 2 10",
) -> CpuCollection:
    samples = parse_sar_cpu_output(output)
    max_cpu = max(sample.cpu_usage for sample in samples)
    return CpuCollection(
        host=host,
        collected_date=collected_date or date.today().isoformat(),
        command=command,
        samples=samples,
        max_cpu=round(max_cpu, 2),
    )


def read_history(history_path: str | Path) -> list[dict[str, float | str]]:
    path = Path(history_path)
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: str | Path, payload: object) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return output_path


def write_collection(path: str | Path, collection: CpuCollection) -> Path:
    payload = asdict(collection)
    return write_json(path, payload)


def update_history(
    history_path: str | Path,
    collection: CpuCollection,
    keep_days: int = 30,
) -> list[dict[str, float | str]]:
    history = read_history(history_path)
    by_date = {str(item["date"]): float(item["max_cpu"]) for item in history}
    current_value = by_date.get(collection.collected_date, 0.0)
    by_date[collection.collected_date] = round(max(current_value, collection.max_cpu), 2)

    updated = [
        {"date": usage_date, "max_cpu": max_cpu}
        for usage_date, max_cpu in sorted(by_date.items())
    ][-keep_days:]
    write_json(history_path, updated)
    return updated


def collect_and_update_history(
    history_path: str | Path = "data/history.json",
    sample_path: str | Path = "data/latest_cpu_sample.json",
    host: str = "local",
    interval: int = 2,
    count: int = 10,
    sar_output: str | None = None,
    collected_date: str | None = None,
) -> CpuCollection:
    command = f"sar -u {interval} {count}"
    output = sar_output if sar_output is not None else run_sar_command(interval, count)
    collection = collect_cpu_from_output(
        output=output,
        host=host,
        collected_date=collected_date,
        command=command,
    )
    write_collection(sample_path, collection)
    update_history(history_path, collection)
    return collection
