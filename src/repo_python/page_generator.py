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


@dataclass(frozen=True)
class CurrentCpuSample:
    label: str
    cpu_usage: float


@dataclass(frozen=True)
class CurrentCpuCollection:
    host: str
    collected_date: str
    command: str
    samples: list[CurrentCpuSample]
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


def load_current_cpu_sample(json_path: str | Path) -> CurrentCpuCollection | None:
    path = Path(json_path)
    if not path.exists():
        return None

    payload = json.loads(path.read_text(encoding="utf-8"))
    samples = [
        CurrentCpuSample(
            label=str(item["label"]),
            cpu_usage=float(item["cpu_usage"]),
        )
        for item in payload.get("samples", [])
    ]
    if not samples:
        return None

    return CurrentCpuCollection(
        host=str(payload["host"]),
        collected_date=str(payload["collected_date"]),
        command=str(payload["command"]),
        samples=samples,
        max_cpu=float(payload["max_cpu"]),
    )


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


def get_trend_summary(records: list[CpuUsageRecord]) -> dict[str, float | int | str]:
    if len(records) < 2:
        return {
            "direction": "Not enough data",
            "difference": 0.0,
            "recent_average": records[0].max_cpu if records else 0.0,
            "previous_average": 0.0,
            "warning_days": 0,
            "critical_days": 0,
        }

    recent_records = records[-7:]
    previous_records = records[-14:-7] or records[:-7]
    recent_average = get_average_cpu(recent_records)
    previous_average = get_average_cpu(previous_records)
    difference = recent_average - previous_average
    if difference > 3:
        direction = "Increasing"
    elif difference < -3:
        direction = "Decreasing"
    else:
        direction = "Stable"

    return {
        "direction": direction,
        "difference": round(difference, 1),
        "recent_average": round(recent_average, 1),
        "previous_average": round(previous_average, 1),
        "warning_days": sum(1 for record in records if 80 <= record.max_cpu < 90),
        "critical_days": sum(1 for record in records if record.max_cpu >= 90),
    }


def build_trend_chart_markup(records: list[CpuUsageRecord]) -> str:
    if not records:
        return ""

    chart_width = 700
    chart_height = 220
    plot_left = 34
    plot_right = 674
    plot_top = 24
    plot_bottom = 176
    plot_width = plot_right - plot_left
    plot_height = plot_bottom - plot_top
    denominator = max(len(records) - 1, 1)
    points: list[tuple[float, float, CpuUsageRecord]] = []

    for index, record in enumerate(records):
        x = plot_left + (index / denominator) * plot_width
        y = plot_bottom - (record.max_cpu / 100) * plot_height
        points.append((x, y, record))

    point_string = " ".join(f"{x:.1f},{y:.1f}" for x, y, _record in points)
    peak_x, peak_y, peak_record = max(points, key=lambda point: point[2].max_cpu)
    latest_x, latest_y, latest_record = points[-1]
    circles = "\n".join(
        f"""          <circle cx="{x:.1f}" cy="{y:.1f}" r="3" class="trend-point {get_status_class(record.max_cpu)}">
            <title>{escape(record.usage_date)}: {record.max_cpu:.1f}%</title>
          </circle>"""
        for x, y, record in points
    )

    def y_for_cpu(cpu_value: float) -> float:
        return plot_bottom - (cpu_value / 100) * plot_height

    return f"""      <div class="trend-chart">
        <svg viewBox="0 0 {chart_width} {chart_height}" role="img" aria-label="30-day CPU trend line chart">
          <line x1="{plot_left}" y1="{y_for_cpu(90):.1f}" x2="{plot_right}" y2="{y_for_cpu(90):.1f}" class="threshold critical" />
          <line x1="{plot_left}" y1="{y_for_cpu(80):.1f}" x2="{plot_right}" y2="{y_for_cpu(80):.1f}" class="threshold warning" />
          <text x="4" y="{y_for_cpu(90) + 4:.1f}" class="axis-label">90%</text>
          <text x="4" y="{y_for_cpu(80) + 4:.1f}" class="axis-label">80%</text>
          <polyline points="{point_string}" class="trend-line" />
{circles}
          <circle cx="{peak_x:.1f}" cy="{peak_y:.1f}" r="6" class="peak-point" />
          <text x="{max(40, peak_x - 46):.1f}" y="{max(16, peak_y - 10):.1f}" class="data-label">Peak {peak_record.max_cpu:.1f}%</text>
          <circle cx="{latest_x:.1f}" cy="{latest_y:.1f}" r="5" class="latest-point" />
          <text x="{max(40, latest_x - 72):.1f}" y="{min(206, latest_y + 22):.1f}" class="data-label">Latest {latest_record.max_cpu:.1f}%</text>
          <text x="{plot_left}" y="206" class="axis-label">{escape(records[0].usage_date)}</text>
          <text x="{plot_right - 78}" y="206" class="axis-label">{escape(records[-1].usage_date)}</text>
        </svg>
      </div>"""


def build_analysis_markup(records: list[CpuUsageRecord]) -> str:
    peak = get_peak_record(records)
    latest = records[-1]
    summary = get_trend_summary(records)
    direction = str(summary["direction"])
    difference = float(summary["difference"])
    difference_text = f"{difference:+.1f}%"
    return f"""      <div class="analysis-grid">
        <article class="analysis-card">
          <span>Trend</span>
          <strong>{escape(direction)}</strong>
          <p>Recent 7-day average is {summary["recent_average"]:.1f}% vs previous 7-day average {summary["previous_average"]:.1f}% ({difference_text}).</p>
        </article>
        <article class="analysis-card">
          <span>Peak</span>
          <strong>{peak.max_cpu:.1f}%</strong>
          <p>Highest daily max was on {escape(peak.usage_date)}.</p>
        </article>
        <article class="analysis-card">
          <span>Thresholds</span>
          <strong>{summary["critical_days"]} critical / {summary["warning_days"]} warning</strong>
          <p>Critical is 90% or higher. Warning is 80% to 89.9%.</p>
        </article>
        <article class="analysis-card">
          <span>Latest</span>
          <strong>{latest.max_cpu:.1f}%</strong>
          <p>Latest daily max is {get_status_class(latest.max_cpu)} for {escape(latest.usage_date)}.</p>
        </article>
      </div>"""


def build_html(
    records: list[CpuUsageRecord],
    title: str = "Host CPU Max Usage",
    subtitle: str = "Current sar sample plus last 30 days of maximum CPU usage.",
    source_label: str = "data/history.json",
    current_sample: CurrentCpuCollection | None = None,
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
    current_markup = build_current_sample_markup(current_sample)
    trend_markup = build_trend_chart_markup(records)
    analysis_markup = build_analysis_markup(records)

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

    .trend-section {{
      margin-top: 18px;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 18px;
      box-shadow: 0 14px 34px rgba(15, 23, 42, .08);
    }}

    .trend-chart {{
      overflow-x: auto;
      margin: 12px 0 16px;
    }}

    .trend-chart svg {{
      display: block;
      min-width: 620px;
      width: 100%;
      height: auto;
    }}

    .trend-line {{
      fill: none;
      stroke: var(--blue);
      stroke-width: 4;
      stroke-linecap: round;
      stroke-linejoin: round;
    }}

    .threshold {{
      stroke-width: 2;
      stroke-dasharray: 6 6;
    }}

    .threshold.warning {{
      stroke: rgba(183, 121, 31, .55);
    }}

    .threshold.critical {{
      stroke: rgba(197, 48, 48, .55);
    }}

    .trend-point {{
      fill: var(--green);
      stroke: #ffffff;
      stroke-width: 2;
    }}

    .trend-point.warning {{
      fill: var(--yellow);
    }}

    .trend-point.critical {{
      fill: var(--red);
    }}

    .peak-point {{
      fill: var(--red);
      stroke: #ffffff;
      stroke-width: 2;
    }}

    .latest-point {{
      fill: var(--blue);
      stroke: #ffffff;
      stroke-width: 2;
    }}

    .axis-label,
    .data-label {{
      fill: var(--muted);
      font-size: 12px;
      font-weight: 800;
    }}

    .analysis-grid {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 10px;
    }}

    .analysis-card {{
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 13px;
      background: #fbfdff;
    }}

    .analysis-card span {{
      display: block;
      color: var(--blue);
      font-size: .78rem;
      font-weight: 850;
      letter-spacing: .04em;
      text-transform: uppercase;
    }}

    .analysis-card strong {{
      display: block;
      margin-top: 4px;
      font-size: 1.05rem;
    }}

    .analysis-card p {{
      margin: 6px 0 0;
      color: var(--muted);
      font-size: .92rem;
    }}

    .current-sar {{
      margin-top: 18px;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 18px;
      box-shadow: 0 14px 34px rgba(15, 23, 42, .08);
    }}

    .section-head {{
      display: flex;
      justify-content: space-between;
      gap: 14px;
      align-items: start;
      margin-bottom: 12px;
    }}

    .section-head h2 {{
      margin: 0;
    }}

    .section-head p {{
      margin: 4px 0 0;
      color: var(--muted);
    }}

    .command-pill {{
      flex: 0 0 auto;
      border-radius: 999px;
      background: #172033;
      color: #dbeafe;
      padding: 7px 10px;
      font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
      font-size: .82rem;
      font-weight: 800;
      white-space: nowrap;
    }}

    .sample-grid {{
      display: grid;
      grid-template-columns: repeat(5, minmax(0, 1fr));
      gap: 10px;
    }}

    .sample-card {{
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 11px;
      background: #fbfdff;
    }}

    .sample-time {{
      display: block;
      color: var(--muted);
      font-size: .82rem;
      font-weight: 800;
    }}

    .sample-value {{
      display: block;
      margin-top: 4px;
      font-size: 1.18rem;
      font-weight: 900;
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

      .section-head {{
        display: block;
      }}

      .command-pill {{
        display: inline-flex;
        margin-top: 8px;
      }}

      .sample-grid {{
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }}

      .analysis-grid {{
        grid-template-columns: 1fr;
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

{current_markup}

    <section class="trend-section" aria-label="CPU trend and analysis">
      <div class="section-head">
        <div>
          <h2>30-Day Trend Chart and Analysis</h2>
          <p>Line chart and summary based on daily maximum CPU history.</p>
        </div>
      </div>
{trend_markup}
{analysis_markup}
    </section>

    <section class="chart" aria-label="CPU usage bar chart">
      <h2>Last 30 Days Max CPU Usage</h2>
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

    <div class="note">Generated on {today} from <code>{escape(source_label)}</code>.</div>
  </main>

  <footer class="wrap">
    Mobile-friendly CPU report published from GitHub using a Python-generated HTML file.
  </footer>
</body>
</html>
"""


def build_current_sample_markup(current_sample: CurrentCpuCollection | None) -> str:
    if current_sample is None:
        return """    <section class="current-sar" aria-label="Current sar output">
      <div class="section-head">
        <div>
          <h2>Current sar -u 2 10 Output</h2>
          <p>No latest sample JSON found yet. Run the collector to populate this section.</p>
        </div>
        <span class="command-pill">sar -u 2 10</span>
      </div>
    </section>"""

    sample_cards = "\n".join(
        f"""        <article class="sample-card">
          <span class="sample-time">{escape(sample.label)}</span>
          <span class="sample-value">{sample.cpu_usage:.1f}%</span>
          <span class="status {get_status_class(sample.cpu_usage)}">{get_status_class(sample.cpu_usage).title()}</span>
        </article>"""
        for sample in current_sample.samples
    )
    return f"""    <section class="current-sar" aria-label="Current sar output">
      <div class="section-head">
        <div>
          <h2>Current sar -u 2 10 Output</h2>
          <p>Host: {escape(current_sample.host)} | Date: {escape(current_sample.collected_date)} | Current sample max: {current_sample.max_cpu:.1f}%</p>
        </div>
        <span class="command-pill">{escape(current_sample.command)}</span>
      </div>
      <div class="sample-grid">
{sample_cards}
      </div>
    </section>"""


def write_html(
    output_path: str | Path,
    data_path: str | Path = "data/history.json",
    sample_path: str | Path = "data/latest_cpu_sample.json",
) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    records = load_cpu_usage(data_path)
    current_sample = load_current_cpu_sample(sample_path)
    path.write_text(
        build_html(records, source_label=str(data_path), current_sample=current_sample),
        encoding="utf-8",
    )
    return path
