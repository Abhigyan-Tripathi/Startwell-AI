"""SQLite persistence layer for daily metrics and tasks."""
import sqlite3
from datetime import date, timedelta
from typing import Optional

from config import settings


class DatabaseManager:
    def __init__(self, db_path: Optional[str] = None):
        self._db_path = db_path or settings.sqlite_path
        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        self._init_schema()

    def _init_schema(self) -> None:
        cursor = self._conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_metrics (
              date               TEXT PRIMARY KEY,
              sleep_hours        REAL DEFAULT 0.0,
              exercise_hours     REAL DEFAULT 0.0,
              productivity_hours REAL DEFAULT 0.0,
              self_help_hours    REAL DEFAULT 0.0
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_tasks (
              date TEXT,
              task TEXT,
              done INTEGER DEFAULT 0,
              PRIMARY KEY (date, task)
            )
        """)
        self._conn.commit()

    def upsert_daily_metrics(self, date_str: str, sleep: float, exercise: float,
                              productivity: float, self_help: float) -> None:
        self._conn.execute("""
            INSERT INTO daily_metrics (date, sleep_hours, exercise_hours, productivity_hours, self_help_hours)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(date) DO UPDATE SET
                sleep_hours        = excluded.sleep_hours,
                exercise_hours     = excluded.exercise_hours,
                productivity_hours = excluded.productivity_hours,
                self_help_hours    = excluded.self_help_hours
        """, (date_str, sleep, exercise, productivity, self_help))
        self._conn.commit()

    def get_weekly_averages(self, start_date: str, end_date: str) -> tuple[float, float, float, float]:
        cursor = self._conn.cursor()
        cursor.execute("""
            SELECT AVG(sleep_hours), AVG(exercise_hours), AVG(productivity_hours), AVG(self_help_hours)
            FROM daily_metrics WHERE date BETWEEN ? AND ?
        """, (start_date, end_date))
        row = cursor.fetchone()
        if row and any(v is not None for v in row):
            return tuple(v or 0.0 for v in row)  # type: ignore
        return (0.0, 0.0, 0.0, 0.0)

    def insert_task(self, date_str: str, task: str) -> None:
        self._conn.execute(
            "INSERT OR IGNORE INTO daily_tasks(date, task, done) VALUES (?, ?, 0)",
            (date_str, task),
        )
        self._conn.commit()

    def bulk_insert_tasks(self, tasks: dict[str, str]) -> None:
        for date_str, task in tasks.items():
            self.insert_task(date_str, task)

    def get_tasks_for_range(self, start_date: str, end_date: str) -> list[tuple[str, str, int]]:
        cursor = self._conn.cursor()
        cursor.execute(
            "SELECT date, task, done FROM daily_tasks WHERE date BETWEEN ? AND ? ORDER BY date",
            (start_date, end_date),
        )
        return cursor.fetchall()

    def get_tasks_for_date(self, date_str: str) -> list[tuple[str, int]]:
        cursor = self._conn.cursor()
        cursor.execute("SELECT task, done FROM daily_tasks WHERE date = ?", (date_str,))
        return cursor.fetchall()

    def set_task_done(self, date_str: str, task: str, done: bool) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO daily_tasks(date, task, done) VALUES (?, ?, ?)",
            (date_str, task, int(done)),
        )
        self._conn.commit()

    @staticmethod
    def last_n_days(anchor: str, n: int = 7) -> list[str]:
        anchor_date = date.fromisoformat(anchor)
        start = anchor_date - timedelta(days=n - 1)
        return [(start + timedelta(days=i)).isoformat() for i in range(n)]
