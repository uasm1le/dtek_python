"""Power Monitor Runner - convenient entry point for cron jobs."""

from src.power_monitor import PowerMonitor


def main():
    """Run power monitor once."""
    monitor = PowerMonitor()
    monitor.run()


if __name__ == "__main__":
    main()
