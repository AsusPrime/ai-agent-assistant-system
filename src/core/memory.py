import os
import sqlite3
import time

from pydantic_ai.messages import ModelMessagesTypeAdapter


class MessageRepository:
    def __init__(self, data_dir: str) -> None:
        data_dir = os.path.expanduser(data_dir)
        os.makedirs(data_dir, exist_ok=True)
        self._db_path = os.path.join(data_dir, "memory.db")
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id  TEXT    NOT NULL,
                    turn_blob   BLOB    NOT NULL,
                    turn_index  INTEGER NOT NULL,
                    ts          REAL    NOT NULL
                )
            """)
            conn.commit()

    def save_turn(self, session_id: str, messages: list) -> None:
        if not messages:
            return
        blob = ModelMessagesTypeAdapter.dump_json(messages)
        with sqlite3.connect(self._db_path) as conn:
            turn_index = conn.execute(
                "SELECT COALESCE(MAX(turn_index), -1) + 1 FROM messages WHERE session_id = ?",
                (session_id,),
            ).fetchone()[0]
            conn.execute(
                "INSERT INTO messages (session_id, turn_blob, turn_index, ts) VALUES (?, ?, ?, ?)",
                (session_id, blob, turn_index, time.time()),
            )
            conn.commit()

    def load_recent(self, n_turns: int = 8) -> list:
        with sqlite3.connect(self._db_path) as conn:
            rows = conn.execute(
                "SELECT turn_blob FROM (SELECT turn_blob, ts FROM messages ORDER BY ts DESC LIMIT ?) ORDER BY ts ASC",
                (n_turns,),
            ).fetchall()

        all_messages: list = []
        for (blob,) in rows:
            turn = ModelMessagesTypeAdapter.validate_json(blob)
            all_messages.extend(turn)

        # History must START with a ModelRequest that contains a user-prompt —
        # not a tool-return. Trimming to recent turns can leave the list starting
        # with a tool-return (kind="request") whose paired tool-call was dropped,
        # which Gemini rejects as "function response without preceding function call".
        while all_messages:
            m = all_messages[0]
            if getattr(m, "kind", None) != "request":
                all_messages.pop(0)
                continue
            parts = getattr(m, "parts", [])
            if any(getattr(p, "part_kind", None) == "user-prompt" for p in parts):
                break
            all_messages.pop(0)

        # Similarly, the tail must not END with an unpaired tool-call —
        # walk back and drop trailing responses that contain tool-call parts
        # without a following request with tool-return.
        while all_messages:
            last = all_messages[-1]
            if getattr(last, "kind", None) == "response":
                parts = getattr(last, "parts", [])
                has_tool_call = any(
                    getattr(p, "part_kind", None) == "tool-call" for p in parts
                )
                if has_tool_call:
                    all_messages.pop()
                    continue
            break

        return all_messages
