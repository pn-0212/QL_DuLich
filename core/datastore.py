from __future__ import annotations

import copy
import json
import os
import sqlite3
from collections.abc import Callable
from datetime import datetime

from core.business_rules import normalize_business_state
from core.security import prepare_password_for_storage
from core.system_rules import CANCEL_BOOKING_STATUSES, apply_system_rules


DEFAULT_DB_FILENAME = "travel_management.db"


class SQLiteDataStore:
    def __init__(
        self,
        path: str,
        rev_path: str | None = None,
        notif_path: str | None = None,
        *,
        db_path: str | None = None,
        default_data: dict | None = None,
        normalize_review_item: Callable | None = None,
        normalize_notification_item: Callable | None = None,
        text_normalizer: Callable | None = None,
    ):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `__init__` (  init  ).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            path: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            rev_path: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            notif_path: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            db_path: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            default_data: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            normalize_review_item: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            normalize_notification_item: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            text_normalizer: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        self.path = path
        self.rev_path = rev_path
        self.notif_path = notif_path
        self.db_path = db_path or os.path.join(os.path.dirname(path), DEFAULT_DB_FILENAME)
        self.default_data = copy.deepcopy(default_data or {"admin": {"username": "admin", "password": "123"}})
        self._normalize_review_item = normalize_review_item
        self._normalize_notification_item = normalize_notification_item
        self._text_normalizer = text_normalizer

        self.data = self._new_data_container()
        self.reviews: list[dict] = []
        self.notifications: list[dict] = []
        self.load()

    def _new_data_container(self) -> dict:
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_new_data_container` ( new data container).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Giá trị theo khai báo kiểu trả về của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        data = copy.deepcopy(self.default_data)
        data.setdefault("hdv", [])
        data.setdefault("tours", [])
        data.setdefault("bookings", [])
        data.setdefault("users", [])
        data.setdefault("admin", {})
        data.setdefault("maVoucher", [])
        return data

    def _connect(self) -> sqlite3.Connection:
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_connect` ( connect).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Giá trị theo khai báo kiểu trả về của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        folder = os.path.dirname(self.db_path)
        if folder and not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _ensure_schema(self, conn: sqlite3.Connection) -> None:
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_ensure_schema` ( ensure schema).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            conn: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Giá trị theo khai báo kiểu trả về của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS app_state (
                state_key TEXT PRIMARY KEY,
                payload TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                migration_name TEXT PRIMARY KEY,
                applied_at TEXT NOT NULL
            )
            """
        )
        conn.commit()

    def _is_initialized(self, conn: sqlite3.Connection) -> bool:
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_is_initialized` ( is initialized).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            conn: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Giá trị theo khai báo kiểu trả về của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        row = conn.execute(
            "SELECT 1 FROM app_state WHERE state_key = ? LIMIT 1",
            ("data",),
        ).fetchone()
        return row is not None

    def _apply_text_normalizer(self, value):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_apply_text_normalizer` ( apply text normalizer).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            value: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        if callable(self._text_normalizer):
            return self._text_normalizer(value)
        return value

    def _normalize_data_payload(self, data: dict) -> dict:
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_normalize_data_payload` ( normalize data payload).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            data: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Giá trị theo khai báo kiểu trả về của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        payload = self._apply_text_normalizer(data)
        if not isinstance(payload, dict):
            payload = {}
        merged = self._new_data_container()
        merged.update(payload)
        system_normalized = apply_system_rules(merged)
        return normalize_business_state(system_normalized)

    def _normalize_collection(self, rows, normalizer: Callable | None):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_normalize_collection` ( normalize collection).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            rows: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            normalizer: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        if not isinstance(rows, list):
            return []
        normalized_rows = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            item = self._apply_text_normalizer(row)
            if callable(normalizer):
                try:
                    item = normalizer(item, self)
                except TypeError:
                    item = normalizer(item)
            if isinstance(item, dict):
                normalized_rows.append(item)
        return normalized_rows

    def _read_legacy_json(self):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_read_legacy_json` ( read legacy json).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        data = self._new_data_container()
        reviews = []
        notifications = []

        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8-sig") as file:
                    loaded = json.load(file)
                if isinstance(loaded, dict):
                    data.update(loaded)
            except (OSError, json.JSONDecodeError):
                pass

        if self.rev_path and os.path.exists(self.rev_path):
            try:
                with open(self.rev_path, "r", encoding="utf-8-sig") as file:
                    loaded_reviews = json.load(file)
                if isinstance(loaded_reviews, list):
                    reviews = loaded_reviews
            except (OSError, json.JSONDecodeError):
                reviews = []

        if self.notif_path and os.path.exists(self.notif_path):
            try:
                with open(self.notif_path, "r", encoding="utf-8-sig") as file:
                    loaded_notifs = json.load(file)
                if isinstance(loaded_notifs, list):
                    notifications = loaded_notifs
            except (OSError, json.JSONDecodeError):
                notifications = []

        return data, reviews, notifications

    def _secure_password_fields(self, data: dict) -> dict:
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_secure_password_fields` ( secure password fields).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            data: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Giá trị theo khai báo kiểu trả về của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        secured = copy.deepcopy(data)
        for guide in secured.get("hdv", []):
            guide["password"] = prepare_password_for_storage(guide.get("password", ""))
        for user in secured.get("users", []):
            user["password"] = prepare_password_for_storage(user.get("password", ""))

        admin = secured.get("admin", {})
        if isinstance(admin, dict):
            admin["password"] = prepare_password_for_storage(admin.get("password", ""))
        return secured

    def _write_payload(self, conn: sqlite3.Connection, key: str, value) -> None:
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_write_payload` ( write payload).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            conn: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            key: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            value: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Giá trị theo khai báo kiểu trả về của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        conn.execute(
            """
            INSERT INTO app_state (state_key, payload, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(state_key) DO UPDATE SET
                payload = excluded.payload,
                updated_at = excluded.updated_at
            """,
            (
                key,
                json.dumps(value, ensure_ascii=False),
                datetime.now().isoformat(timespec="seconds"),
            ),
        )

    def _bootstrap_from_legacy_json(self, conn: sqlite3.Connection) -> None:
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_bootstrap_from_legacy_json` ( bootstrap from legacy json).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            conn: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Giá trị theo khai báo kiểu trả về của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        raw_data, raw_reviews, raw_notifications = self._read_legacy_json()
        normalized_data = self._normalize_data_payload(raw_data)
        secured_data = self._secure_password_fields(normalized_data)

        self._write_payload(conn, "data", secured_data)
        self._write_payload(
            conn,
            "reviews",
            self._normalize_collection(raw_reviews, self._normalize_review_item),
        )
        self._write_payload(
            conn,
            "notifications",
            self._normalize_collection(raw_notifications, self._normalize_notification_item),
        )
        conn.execute(
            """
            INSERT OR IGNORE INTO schema_migrations (migration_name, applied_at)
            VALUES (?, ?)
            """,
            ("json_to_sqlite", datetime.now().isoformat(timespec="seconds")),
        )
        conn.commit()

    def _read_payload(self, conn: sqlite3.Connection, key: str, fallback):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_read_payload` ( read payload).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            conn: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            key: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            fallback: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        row = conn.execute(
            "SELECT payload FROM app_state WHERE state_key = ?",
            (key,),
        ).fetchone()
        if row is None:
            return fallback
        try:
            return json.loads(row["payload"])
        except (TypeError, json.JSONDecodeError):
            return fallback

    def load(self) -> None:
        """
        Mục đích:
            Thực hiện xử lý cho hàm `load` (load).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Giá trị theo khai báo kiểu trả về của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        with self._connect() as conn:
            self._ensure_schema(conn)
            if not self._is_initialized(conn):
                self._bootstrap_from_legacy_json(conn)

            self.data = self._normalize_data_payload(self._read_payload(conn, "data", self._new_data_container()))
            self.reviews = self._normalize_collection(
                self._read_payload(conn, "reviews", []),
                self._normalize_review_item,
            )
            self.notifications = self._normalize_collection(
                self._read_payload(conn, "notifications", []),
                self._normalize_notification_item,
            )

    def save(self) -> None:
        """
        Mục đích:
            Thực hiện xử lý cho hàm `save` (save).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Giá trị theo khai báo kiểu trả về của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        normalized_data = self._normalize_data_payload(self.data)
        secured_data = self._secure_password_fields(normalized_data)

        with self._connect() as conn:
            self._ensure_schema(conn)
            self._write_payload(conn, "data", secured_data)
            self._write_payload(conn, "reviews", self.reviews)
            self._write_payload(conn, "notifications", self.notifications)
            conn.commit()

        self.data = secured_data

    @property
    def list_hdv(self):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `list_hdv` (list hdv).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        return self.data["hdv"]

    @property
    def list_tours(self):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `list_tours` (list tours).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        return self.data["tours"]

    @property
    def list_bookings(self):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `list_bookings` (list bookings).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        return self.data["bookings"]

    @property
    def list_users(self):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `list_users` (list users).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        return self.data["users"]

    @property
    def list_reviews(self):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `list_reviews` (list reviews).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        return self.reviews

    @property
    def list_notifications(self):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `list_notifications` (list notifications).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        return self.notifications

    @property
    def list_vouchers(self):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `list_vouchers` (list vouchers).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        return self.data["maVoucher"]

    def find_admin(self, username):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `find_admin` (find admin).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            username: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        admin = self.data.get("admin", {})
        if isinstance(admin, dict) and str(admin.get("username", "")).strip() == str(username or "").strip():
            return admin
        return None

    def find_user(self, username):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `find_user` (find user).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            username: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        normalized = str(username or "").strip().lower()
        return next((u for u in self.list_users if str(u.get("username", "")).strip().lower() == normalized), None)

    def find_hdv(self, ma_hdv):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `find_hdv` (find hdv).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            ma_hdv: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        normalized = str(ma_hdv or "").strip().upper()
        return next((h for h in self.list_hdv if str(h.get("maHDV", "")).strip().upper() == normalized), None)

    def find_tour(self, ma_tour):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `find_tour` (find tour).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            ma_tour: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        normalized = str(ma_tour or "").strip().upper()
        return next((t for t in self.list_tours if str(t.get("ma", "")).strip().upper() == normalized), None)

    def find_voucher(self, code):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `find_voucher` (find voucher).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            code: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        normalized = str(code or "").strip().upper()
        if not normalized:
            return None
        return next(
            (
                voucher
                for voucher in self.list_vouchers
                if str(voucher.get("maVoucher", "")).strip().upper() == normalized
            ),
            None,
        )

    def get_bookings_by_tour(self, ma_tour):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `get_bookings_by_tour` (get bookings by tour).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            ma_tour: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        normalized = str(ma_tour or "").strip().upper()
        return [booking for booking in self.list_bookings if str(booking.get("maTour", "")).strip().upper() == normalized]

    def get_occupied_seats(self, ma_tour):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `get_occupied_seats` (get occupied seats).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            ma_tour: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        total = 0
        for booking in self.get_bookings_by_tour(ma_tour):
            refund_status = str(booking.get("trangThaiHoanTien", "")).strip()
            if booking.get("trangThai") in CANCEL_BOOKING_STATUSES and refund_status != "Từ chối":
                continue
            try:
                total += int(str(booking.get("soNguoi", 0)).strip())
            except (TypeError, ValueError):
                continue
        return total
