import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from repo_python.main import greeting
from repo_python.cpu_collector import (
    collect_and_update_history,
    collect_cpu_from_output,
    parse_sar_cpu_output,
    update_history,
)
from repo_python.page_generator import (
    CpuUsageRecord,
    build_html,
    get_average_cpu,
    get_date_range_label,
    get_peak_record,
    get_status_class,
    get_trend_summary,
    load_current_cpu_sample,
    load_cpu_usage,
    write_html,
)


class GreetingTests(unittest.TestCase):
    def test_default_greeting(self) -> None:
        self.assertEqual(greeting(), "Hello from Python project")

    def test_custom_greeting(self) -> None:
        self.assertEqual(greeting("Codex"), "Hello from Codex")


class PageGeneratorTests(unittest.TestCase):
    def test_load_cpu_usage_reads_json(self) -> None:
        records = load_cpu_usage("data/history.json")

        self.assertEqual(len(records), 30)
        self.assertEqual(records[0].usage_date, "2026-05-01")
        self.assertEqual(records[-1].usage_date, "2026-05-30")

    def test_build_html_contains_title(self) -> None:
        records = [CpuUsageRecord("2026-05-01", 82.5)]

        html = build_html(records, title="My Test Page")

        self.assertIn("<title>My Test Page</title>", html)
        self.assertIn("<h1>My Test Page</h1>", html)
        self.assertIn("82.5%", html)
        self.assertIn("Last 30 Days Max CPU Usage", html)
        self.assertIn("30-Day Trend Chart and Analysis", html)
        self.assertIn(
            "30-day history date range: 2026-05-01 to 2026-05-01 (Asia/Kuala_Lumpur)",
            html,
        )

    def test_load_current_cpu_sample_reads_json(self) -> None:
        sample = load_current_cpu_sample("data/latest_cpu_sample.json")

        self.assertIsNotNone(sample)
        assert sample is not None
        self.assertEqual(sample.command, "sar -u 2 10")
        self.assertGreater(len(sample.samples), 0)

    def test_build_html_contains_current_sar_output(self) -> None:
        records = [CpuUsageRecord("2026-05-01", 82.5)]
        sample = load_current_cpu_sample("data/latest_cpu_sample.json")

        html = build_html(records, current_sample=sample)

        self.assertIn("Current sar -u 2 10 Output", html)
        self.assertIn("Current sample max", html)
        self.assertIn("Asia/Kuala_Lumpur", html)

    def test_peak_and_average_cpu(self) -> None:
        records = [
            CpuUsageRecord("2026-05-01", 50.0),
            CpuUsageRecord("2026-05-02", 95.0),
            CpuUsageRecord("2026-05-03", 80.0),
        ]

        self.assertEqual(get_peak_record(records).max_cpu, 95.0)
        self.assertEqual(get_average_cpu(records), 75.0)

    def test_trend_summary(self) -> None:
        records = [
            CpuUsageRecord(f"2026-05-{day:02d}", float(day))
            for day in range(1, 15)
        ]

        summary = get_trend_summary(records)

        self.assertEqual(summary["direction"], "Increasing")
        self.assertEqual(summary["recent_average"], 11.0)
        self.assertEqual(summary["previous_average"], 4.0)

    def test_date_range_label(self) -> None:
        records = [
            CpuUsageRecord("2026-05-01", 50.0),
            CpuUsageRecord("2026-05-30", 80.0),
        ]

        self.assertEqual(get_date_range_label(records), "2026-05-01 to 2026-05-30")

    def test_status_class(self) -> None:
        self.assertEqual(get_status_class(70.0), "normal")
        self.assertEqual(get_status_class(80.0), "warning")
        self.assertEqual(get_status_class(90.0), "critical")

    def test_write_html_creates_file(self) -> None:
        with TemporaryDirectory() as temp_dir:
            data_path = Path(temp_dir) / "cpu_usage.json"
            output_path = Path(temp_dir) / "docs" / "index.html"
            data_path.write_text('[{"date": "2026-05-01", "max_cpu": 72.5}]')

            written_path = write_html(output_path, data_path)

            self.assertEqual(written_path, output_path)
            self.assertTrue(output_path.exists())
            self.assertIn("Host CPU Max Usage", output_path.read_text())


class CpuCollectorTests(unittest.TestCase):
    def test_parse_sar_cpu_output(self) -> None:
        sar_output = Path("tests/fixtures/sar_u_sample.txt").read_text()

        samples = parse_sar_cpu_output(sar_output)

        self.assertEqual(len(samples), 5)
        self.assertEqual(samples[0].cpu_usage, 17.85)
        self.assertEqual(samples[2].cpu_usage, 56.6)

    def test_collect_cpu_from_output_gets_max_cpu(self) -> None:
        sar_output = Path("tests/fixtures/sar_u_sample.txt").read_text()

        collection = collect_cpu_from_output(
            sar_output,
            host="local-test",
            collected_date="2026-05-30",
        )

        self.assertEqual(collection.host, "local-test")
        self.assertEqual(collection.collected_date, "2026-05-30")
        self.assertEqual(collection.max_cpu, 56.6)

    def test_update_history_keeps_daily_max(self) -> None:
        with TemporaryDirectory() as temp_dir:
            history_path = Path(temp_dir) / "history.json"
            history_path.write_text('[{"date": "2026-05-30", "max_cpu": 40.0}]')
            collection = collect_cpu_from_output(
                Path("tests/fixtures/sar_u_sample.txt").read_text(),
                collected_date="2026-05-30",
            )

            history = update_history(history_path, collection)

            self.assertEqual(history, [{"date": "2026-05-30", "max_cpu": 56.6}])

    def test_collect_and_update_history_writes_files(self) -> None:
        with TemporaryDirectory() as temp_dir:
            history_path = Path(temp_dir) / "history.json"
            sample_path = Path(temp_dir) / "latest_cpu_sample.json"
            sar_output = Path("tests/fixtures/sar_u_sample.txt").read_text()

            collection = collect_and_update_history(
                history_path=history_path,
                sample_path=sample_path,
                host="local-test",
                sar_output=sar_output,
                collected_date="2026-05-30",
            )

            self.assertEqual(collection.max_cpu, 56.6)
            self.assertTrue(history_path.exists())
            self.assertTrue(sample_path.exists())
            self.assertIn("local-test", sample_path.read_text())


if __name__ == "__main__":
    unittest.main()
