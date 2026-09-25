import base64
import json
import os
import random
import sqlite3
import time
from datetime import datetime

import webview

from Utility.ChartImaging import generateChart
from Utility.Pannel import Pannel


DEFAULT_TICKERS = ["TEM"]
DEFAULT_BARS = 500
DEFAULT_AGENTS = 5
DEFAULT_WORKERS = 5

ROOT = os.path.dirname(os.path.abspath(__file__))
EXAMPLES_DIR = os.path.join(ROOT, "Examples")
DATABASE_PATH = os.path.join(ROOT, "Databases", "analysis.db")
HTML_FILE = os.path.join(ROOT, "dashboard.html")


def connect_db():
    if not os.path.exists(DATABASE_PATH):
        raise FileNotFoundError(
            f"Database not found: {DATABASE_PATH}. "
            "Run Databases/CreateDatabase.py first."
        )

    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def get_or_create_ticker(conn, ticker):
    row = conn.execute(
        "SELECT TICKER_ID FROM Tickers WHERE TICKER = ?",
        (ticker,),
    ).fetchone()

    if row:
        return row["TICKER_ID"]

    cursor = conn.execute(
        "INSERT INTO Tickers (TICKER) VALUES (?)",
        (ticker,),
    )
    return cursor.lastrowid


def sample_examples(direction, count=4):
    if not os.path.isdir(EXAMPLES_DIR):
        raise FileNotFoundError(f"Examples folder not found: {EXAMPLES_DIR}")

    prefix = "BullReversionSetup" if direction == "bull" else "BearReversionSetup"

    files = [
        os.path.join(EXAMPLES_DIR, filename)
        for filename in os.listdir(EXAMPLES_DIR)
        if filename.startswith(prefix) and filename.lower().endswith(".png")
    ]

    if len(files) < count:
        raise ValueError(
            f"Only found {len(files)} {direction} examples; {count} are required."
        )

    return random.sample(files, count)


def image_bytes_to_data_uri(image_bytes):
    if not image_bytes:
        return None

    encoded = base64.b64encode(image_bytes).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def parse_json(value, default):
    if not value:
        return default

    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return default


def insert_run(
    ticker,
    run_name,
    run_range,
    agent_count,
    worker_count,
    run_time,
    image_bytes,
    status,
    direction,
    bb_percent,
    score,
    score_std,
    metrics,
    examples,
    error,
    duration_seconds,
    agent_outputs,
):
    with connect_db() as conn:
        ticker_id = get_or_create_ticker(conn, ticker)

        cursor = conn.execute(
            """
            INSERT INTO TickerRuns (
                TICKER_ID,
                RUN_NAME,
                START_DATETIME,
                END_DATETIME,
                BAR_COUNT,
                AGENT_COUNT,
                WORKER_COUNT,
                RUN_TIME,
                RUN_IMAGE,
                RUN_STATUS,
                DIRECTION,
                BB_PERCENT,
                SCORE,
                SCORE_STD,
                METRICS_JSON,
                EXAMPLES_JSON,
                ERROR,
                DURATION_SECONDS
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ticker_id,
                run_name,
                run_range.get("startDateTime") if run_range else None,
                run_range.get("endDateTime") if run_range else None,
                run_range.get("barCount") if run_range else None,
                agent_count,
                worker_count,
                run_time,
                sqlite3.Binary(image_bytes) if image_bytes else None,
                status,
                direction,
                bb_percent,
                score,
                score_std,
                json.dumps(metrics) if metrics else None,
                json.dumps(examples) if examples else None,
                error,
                duration_seconds,
            ),
        )

        run_id = cursor.lastrowid

        for agent in agent_outputs:
            conn.execute(
                """
                INSERT INTO PanelOutputs (
                    RUN_ID,
                    AGENT_NUMBER,
                    AGENT_SCORE,
                    PROMPT,
                    RESPONSE
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    agent["agentNumber"],
                    agent.get("score"),
                    agent["prompt"],
                    agent["response"],
                ),
            )

        return run_id


def row_to_run(row, include_image=False, include_panel=False):
    run = {
        "id": row["RUN_ID"],
        "ticker": row["TICKER"],
        "runName": row["RUN_NAME"],
        "startDateTime": row["START_DATETIME"],
        "endDateTime": row["END_DATETIME"],
        "barCount": row["BAR_COUNT"],
        "agentCount": row["AGENT_COUNT"],
        "workerCount": row["WORKER_COUNT"],
        "timestamp": row["RUN_TIME"],
        "status": row["RUN_STATUS"],
        "direction": row["DIRECTION"],
        "bbPercent": row["BB_PERCENT"],
        "score": row["SCORE"],
        "std": row["SCORE_STD"],
        "metrics": parse_json(row["METRICS_JSON"], {}),
        "examples": parse_json(row["EXAMPLES_JSON"], []),
        "error": row["ERROR"],
        "durationSeconds": row["DURATION_SECONDS"],
    }

    if include_image:
        run["chartDataUri"] = image_bytes_to_data_uri(row["RUN_IMAGE"])

    if include_panel:
        with connect_db() as conn:
            panel_rows = conn.execute(
                """
                SELECT
                    PANEL_OUTPUT_ID,
                    AGENT_NUMBER,
                    AGENT_SCORE,
                    PROMPT,
                    RESPONSE
                FROM PanelOutputs
                WHERE RUN_ID = ?
                ORDER BY AGENT_NUMBER
                """,
                (row["RUN_ID"],),
            ).fetchall()

        outputs = []
        for panel_row in panel_rows:
            outputs.append({
                "panelOutputId": panel_row["PANEL_OUTPUT_ID"],
                "agentNumber": panel_row["AGENT_NUMBER"],
                "score": panel_row["AGENT_SCORE"],
                "prompt": panel_row["PROMPT"],
                "response": panel_row["RESPONSE"],
                "visual": parse_json(panel_row["RESPONSE"], {}),
            })

        run["panelOutputs"] = outputs

    return run


class Api:
    def get_initial_state(self):
        return {
            "defaultTickers": DEFAULT_TICKERS,
            "defaultBars": DEFAULT_BARS,
            "defaultAgents": DEFAULT_AGENTS,
            "defaultWorkers": DEFAULT_WORKERS,
            "runs": self._summary_list(),
            "stats": self._overall_stats(),
        }

    def get_run(self, run_id):
        try:
            run_id = int(run_id)

            with connect_db() as conn:
                row = conn.execute(
                    """
                    SELECT TickerRuns.*, Tickers.TICKER
                    FROM TickerRuns
                    JOIN Tickers ON Tickers.TICKER_ID = TickerRuns.TICKER_ID
                    WHERE RUN_ID = ?
                    """,
                    (run_id,),
                ).fetchone()

            if not row:
                return {"ok": False, "error": "Run not found."}

            return {
                "ok": True,
                "run": row_to_run(row, include_image=True, include_panel=True),
            }

        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def run_analysis(
        self,
        ticker,
        bars=DEFAULT_BARS,
        agents=DEFAULT_AGENTS,
        workers=DEFAULT_WORKERS,
    ):
        started_perf = time.perf_counter()
        run_time = datetime.now().isoformat(timespec="seconds")

        ticker = str(ticker or "").strip().upper()

        try:
            bars = int(bars)
            agents = int(agents)
            workers = int(workers)
        except (TypeError, ValueError):
            return {
                "ok": False,
                "error": "Bars, agents, and workers must be integers.",
            }

        if not ticker:
            return {"ok": False, "error": "Ticker is required."}

        if bars < 250:
            return {"ok": False, "error": "Lookback must be at least 250 bars."}

        if agents < 1:
            return {"ok": False, "error": "Agents must be at least 1."}

        if workers < 1:
            return {"ok": False, "error": "Workers must be at least 1."}

        if workers > agents:
            return {
                "ok": False,
                "error": "Workers cannot be greater than agents.",
            }

        image_bytes = None
        metrics = {}
        run_range = None
        direction = None
        bb_percent = None
        score = None
        score_std = None
        examples = []
        agent_outputs = []
        status = "error"
        error = None

        try:
            image_bytes, metrics, run_range = generateChart(ticker, bars=bars)

            bb_percent = metrics["currentOneHourBollingerBandPercent"]

            if bb_percent < 0.15:
                direction = "bull"
            elif bb_percent > 0.85:
                direction = "bear"
            else:
                direction = "neutral"
                status = "skipped"

            if status != "skipped":
                example_paths = sample_examples(direction, 4)
                examples = [os.path.basename(path) for path in example_paths]

                pannel = Pannel(
                    count=agents,
                    workers=workers,
                )

                result = pannel.rank(
                    ticker,
                    image_bytes,
                    metrics,
                    example_paths,
                )

                score = float(result["score"])
                score_std = float(result.get("std", 0))
                agent_outputs = result.get("agents", [])
                status = "complete"

        except Exception as exc:
            error = str(exc)
            status = "error"

        duration_seconds = round(time.perf_counter() - started_perf, 3)
        run_name = f"{ticker} {run_time}"

        try:
            run_id = insert_run(
                ticker=ticker,
                run_name=run_name,
                run_range=run_range,
                agent_count=agents,
                worker_count=workers,
                run_time=run_time,
                image_bytes=image_bytes,
                status=status,
                direction=direction,
                bb_percent=bb_percent,
                score=score,
                score_std=score_std,
                metrics=metrics,
                examples=examples,
                error=error,
                duration_seconds=duration_seconds,
                agent_outputs=agent_outputs,
            )
        except Exception as exc:
            return {
                "ok": False,
                "error": f"Could not save run: {exc}",
            }

        run_response = self.get_run(run_id)

        return {
            "ok": status != "error",
            "error": error,
            "run": run_response.get("run"),
            "runs": self._summary_list(),
            "stats": self._overall_stats(),
        }

    def delete_run(self, run_id):
        try:
            run_id = int(run_id)

            with connect_db() as conn:
                cursor = conn.execute(
                    "DELETE FROM TickerRuns WHERE RUN_ID = ?",
                    (run_id,),
                )

                if cursor.rowcount == 0:
                    return {"ok": False, "error": "Run not found."}

            return {
                "ok": True,
                "runs": self._summary_list(),
                "stats": self._overall_stats(),
            }

        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def _summary_list(self):
        with connect_db() as conn:
            rows = conn.execute(
                """
                SELECT TickerRuns.*, Tickers.TICKER
                FROM TickerRuns
                JOIN Tickers ON Tickers.TICKER_ID = TickerRuns.TICKER_ID
                ORDER BY RUN_ID DESC
                """
            ).fetchall()

        return [row_to_run(row) for row in rows]

    def _overall_stats(self):
        with connect_db() as conn:
            row = conn.execute(
                """
                SELECT
                    COUNT(*) AS TOTAL_RUNS,
                    SUM(CASE WHEN RUN_STATUS = 'complete' THEN 1 ELSE 0 END) AS COMPLETED,
                    AVG(CASE WHEN RUN_STATUS = 'complete' THEN SCORE END) AS AVERAGE_SCORE,
                    SUM(CASE WHEN DIRECTION = 'bull' THEN 1 ELSE 0 END) AS BULL_COUNT,
                    SUM(CASE WHEN DIRECTION = 'bear' THEN 1 ELSE 0 END) AS BEAR_COUNT
                FROM TickerRuns
                """
            ).fetchone()

        return {
            "totalRuns": row["TOTAL_RUNS"] or 0,
            "completed": row["COMPLETED"] or 0,
            "averageScore": row["AVERAGE_SCORE"],
            "bull": row["BULL_COUNT"] or 0,
            "bear": row["BEAR_COUNT"] or 0,
        }


def load_html():
    with open(HTML_FILE, "r", encoding="utf-8") as file:
        return file.read()


if __name__ == "__main__":
    api = Api()

    webview.create_window(
        "Mean Reversion Run Viewer",
        html=load_html(),
        js_api=api,
        width=1450,
        height=900,
        min_size=(1050, 700),
    )

    webview.start()
