import os
import sqlite3


DATABASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(DATABASE_DIR, "analysis.db")


if os.path.exists(DATABASE_PATH):
    os.remove(DATABASE_PATH)
    print("Deleted old database.")


conn = sqlite3.connect(DATABASE_PATH)
conn.execute("PRAGMA foreign_keys = ON")
cursor = conn.cursor()


cursor.execute("""
CREATE TABLE Tickers (
    TICKER_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    TICKER TEXT NOT NULL UNIQUE
)
""")


cursor.execute("""
CREATE TABLE TickerRuns (
    RUN_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    TICKER_ID INTEGER NOT NULL,

    RUN_NAME TEXT,
    START_DATETIME TEXT,
    END_DATETIME TEXT,
    BAR_COUNT INTEGER,

    AGENT_COUNT INTEGER NOT NULL,
    WORKER_COUNT INTEGER NOT NULL,

    RUN_TIME TEXT NOT NULL,
    RUN_IMAGE BLOB,

    RUN_STATUS TEXT NOT NULL,
    DIRECTION TEXT,
    BB_PERCENT REAL,
    SCORE REAL,
    SCORE_STD REAL,

    METRICS_JSON TEXT,
    EXAMPLES_JSON TEXT,
    ERROR TEXT,
    DURATION_SECONDS REAL,

    FOREIGN KEY (TICKER_ID)
        REFERENCES Tickers(TICKER_ID)
        ON DELETE CASCADE,

    CHECK (AGENT_COUNT >= 1),
    CHECK (WORKER_COUNT >= 1),
    CHECK (WORKER_COUNT <= AGENT_COUNT)
)
""")


cursor.execute("""
CREATE TABLE PanelOutputs (
    PANEL_OUTPUT_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    RUN_ID INTEGER NOT NULL,

    AGENT_NUMBER INTEGER NOT NULL,
    AGENT_SCORE REAL,

    PROMPT TEXT NOT NULL,
    RESPONSE TEXT NOT NULL,

    FOREIGN KEY (RUN_ID)
        REFERENCES TickerRuns(RUN_ID)
        ON DELETE CASCADE,

    UNIQUE (RUN_ID, AGENT_NUMBER)
)
""")


conn.commit()
conn.close()

print("Fresh database created:")
print(DATABASE_PATH)
