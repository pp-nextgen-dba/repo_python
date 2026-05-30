from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from html import escape
import json
from pathlib import Path


@dataclass(frozen=True)
class CpuUsageRecord:
    usage_date: str
    max_cpu: float


def load_cpu_usage(json_path: str | Path) -> list[CpuUsageRecord]:
    path = Path(json_path)
    raw_records = json.loads(path.read_text(encoding="utf-8"))

    records = [
        CpuUsageRecord(
            usage_date=str(item["date"]),
            max_cpu=float(item["max_cpu"]),
        )
        for item in raw_records
    ]
    return sorted(records, key=lambda record: record.usage_date)


def get_peak_record(records: list[CpuUsageRecord]) -> CpuUsageRecord:
    if not records:
        raise ValueError("CPU usage data is empty")
    return max(records, key=lambda record: record.max_cpu)


def get_average_cpu(records: list[CpuUsageRecord]) -> float:
    if not records:
        raise ValueError("CPU usage data is empty")
    return sum(record.max_cpu for record in records) / len(records)


def get_status_class(cpu_value: float) -> str:
    if cpu_value >= 90:
        return "critical"
    if cpu_value >= 80:
        return "warning"
    return "normal"


def build_html(
    records: list[CpuUsageRecord],
    title: str = "Host CPU Max Usage",
    subtitle: str = "30-day maximum CPU usage generated from JSON data.",
) -> str:
    peak = get_peak_record(records)
    average = get_average_cpu(records)
    latest = records[-1]

    row_markup = "\n".join(
        f"""          <tr>
            <td>{escape(record.usage_date)}</td>
            <td>
              <div class="cpu-cell">
                <span>{record.max_cpu:.1f}%</span>
                <span class="status {get_status_class(record.max_cpu)}">{get_status_class(record.max_cpu).title()}</span>
              </div>
            </td>
          </tr>"""
        for record in records
    )
    bar_markup = "\n".join(
        f"""        <div class="bar-row">
          <span class="bar-date">{escape(record.usage_date[5:])}</span>
          <div class="bar-track">
            <div class="bar-fill {get_status_class(record.max_cpu)}" style="width: {record.max_cpu:.1f}%"></div>
          </div>
          <span class="bar-value">{record.max_cpu:.1f}%</span>
        </div>"""
        for record in records
    )

    today = date.today().isoformat()
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{escape(title)}</title>
  <style>
    :root {{
      --bg: #f4f7fb;
      --ink: #172033;
      --muted: #5f6f89;
      --panel: #ffffff;
      --line: #d9e2ef;
      --blue: #2563eb;
      --green: #17803d;
      --yellow: #b7791f;
      --red: #c53030;
      --soft-green: #ecfdf3;
      --soft-yellow: #fffbeb;
      --soft-red: #fff1f2;
    }}

    * {{
      box-sizing: border-box;
    }}

    body {{
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
      background: var(--bg);
      color: var(--ink);
      line-height: 1.65;
    }}

    header {{
      background: linear-gradient(135deg, #0f172a, #1d4ed8);
      color: white;
      padding: 56px 20px;
    }}

    .wrap {{
      width: min(960px, calc(100% - 32px));
      margin: 0 auto;
    }}

    h1 {{
      margin: 0;
      font-size: clamp(2rem, 7vw, 4rem);
      line-height: 1.05;
    }}

    .subtitle {{
      max-width: 720px;
      margin: 14px 0 0;
      color: #dbeafe;
      font-size: 1.1rem;
    }}

    main {{
      padding: 28px 0 48px;
    }}

    .summary-grid {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 16px;
    }}

    .card {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 20px;
      box-shadow: 0 14px 34px rgba(15, 23, 42, .08);
    }}

    .card h2 {{
      margin: 0 0 8px;
      font-size: 1.2rem;
    }}

    .card p {{
      margin: 0;
      color: var(--muted);
    }}

    .metric {{
      display: block;
      margin-top: 8px;
      font-size: 2rem;
      font-weight: 900;
      color: var(--ink);
    }}

    .chart {{
      margin-top: 18px;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 18px;
      box-shadow: 0 14px 34px rgba(15, 23, 42, .08);
    }}

    .bar-row {{
      display: grid;
      grid-template-columns: 54px 1fr 64px;
      gap: 10px;
      align-items: center;
      margin: 9px 0;
      font-size: .92rem;
    }}

    .bar-date {{
      color: var(--muted);
      font-weight: 700;
    }}

    .bar-track {{
      min-width: 0;
      height: 13px;
      overflow: hidden;
      border-radius: 999px;
      background: #e5edf7;
    }}

    .bar-fill {{
      height: 100%;
      border-radius: 999px;
      background: var(--green);
    }}

    .bar-fill.warning {{
      background: var(--yellow);
    }}

    .bar-fill.critical {{
      background: var(--red);
    }}

    .bar-value {{
      text-align: right;
      font-weight: 800;
    }}

    .table-wrap {{
      margin-top: 18px;
      overflow-x: auto;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: 0 14px 34px rgba(15, 23, 42, .08);
    }}

    table {{
      width: 100%;
      border-collapse: collapse;
    }}

    th,
    td {{
      padding: 12px 14px;
      border-bottom: 1px solid var(--line);
      text-align: left;
    }}

    th {{
      background: #eaf2ff;
      font-size: .84rem;
      letter-spacing: .04em;
      text-transform: uppercase;
    }}

    tr:last-child td {{
      border-bottom: 0;
    }}

    .cpu-cell {{
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: center;
      font-weight: 800;
    }}

    .status {{
      border-radius: 999px;
      padding: 4px 9px;
      font-size: .78rem;
      font-weight: 850;
      background: var(--soft-green);
      color: var(--green);
    }}

    .status.warning {{
      background: var(--soft-yellow);
      color: var(--yellow);
    }}

    .status.critical {{
      background: var(--soft-red);
      color: var(--red);
    }}

    .note {{
      margin-top: 18px;
      border-left: 5px solid var(--green);
      background: #ecfdf3;
      border-radius: 8px;
      padding: 14px 16px;
      font-weight: 700;
    }}

    footer {{
      color: var(--muted);
      padding: 0 0 36px;
      text-align: center;
    }}

    @media (max-width: 760px) {{
      header {{
        padding: 40px 18px;
      }}

      .summary-grid {{
        grid-template-columns: 1fr;
      }}

      .bar-row {{
        grid-template-columns: 46px 1fr 56px;
        gap: 8px;
      }}

      th,
      td {{
        padding: 10px;
      }}
    }}
  </style>
</head>
<body>
  <header>
    <div class="wrap">
      <h1>{escape(title)}</h1>
      <p class="subtitle">{escape(subtitle)}</p>
    </div>
  </header>

  <main class="wrap">
    <section class="summary-grid">
      <article class="card">
        <h2>Highest CPU</h2>
        <p>{escape(peak.usage_date)}</p>
        <span class="metric">{peak.max_cpu:.1f}%</span>
      </article>
      <article class="card">
        <h2>30-Day Average</h2>
        <p>Average of daily maximum CPU values</p>
        <span class="metric">{average:.1f}%</span>
      </article>
      <article class="card">
        <h2>Latest Day</h2>
        <p>{escape(latest.usage_date)}</p>
        <span class="metric">{latest.max_cpu:.1f}%</span>
      </article>
    </section>

    <section class="chart" aria-label="CPU usage bar chart">
      <h2>Daily Max CPU Usage</h2>
{bar_markup}
    </section>

    <section class="table-wrap" aria-label="CPU usage table">
      <table>
        <thead>
          <tr>
            <th>Date</th>
            <th>Max CPU</th>
          </tr>
        </thead>
        <tbody>
{row_markup}
        </tbody>
      </table>
    </section>

    <div class="note">Generated on {today} from <code>data/cpu_usage.json</code>.</div>
  </main>

  <footer class="wrap">
    Mobile-friendly CPU report published from GitHub using a Python-generated HTML file.
  </footer>
</body>
</html>
"""


def write_html(output_path: str | Path, data_path: str | Path = "data/cpu_usage.json") -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    records = load_cpu_usage(data_path)
    path.write_text(build_html(records), encoding="utf-8")
    return path
