from __future__ import annotations

from dataclasses import dataclass

from core.activity_log import write_activity_log
from core.security import password_matches, prepare_password_for_storage, upgrade_password_hash
from core.validation import (
    is_valid_fullname,
    is_valid_password,
    is_valid_phone,
    is_valid_username,
    normalize_fullname,
    normalize_phone,
    normalize_username,
)


@dataclass(slots=True)
class ServiceResult:
    success: bool
    message: str
    level: str = "info"
    username: str = ""
    display_name: str = ""
    role: str = ""


class AuthService:
    def __init__(self, datastore):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `__init__` (  init  ).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        self.datastore = datastore

    def authenticate(self, role: str, username: str, password: str) -> ServiceResult:
        """
        Mục đích:
            Thực hiện xử lý cho hàm `authenticate` (authenticate).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            role: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            username: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            password: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Giá trị theo khai báo kiểu trả về của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        normalized_username = normalize_username(username)

        if not normalized_username or not str(password or "").strip():
            return ServiceResult(False, "Vui lòng nhập tài khoản và mật khẩu.", level="warning")

        self.datastore.load()
        record = self._resolve_account(role, normalized_username)

        if not record:
            write_activity_log(
                action="LOGIN",
                actor=normalized_username,
                role=role,
                status="FAILED",
                detail="Không tìm thấy tài khoản.",
                datastore=self.datastore,
            )
            return ServiceResult(False, "Sai tài khoản hoặc mật khẩu!", level="error")

        stored_password = record.get("password", "")
        if not password_matches(stored_password, password):
            write_activity_log(
                action="LOGIN",
                actor=normalized_username,
                role=role,
                status="FAILED",
                detail="Mật khẩu không hợp lệ.",
                datastore=self.datastore,
            )
            return ServiceResult(False, "Sai tài khoản hoặc mật khẩu!", level="error")

        migrated = False
        secured_password = upgrade_password_hash(stored_password, password)
        if secured_password and secured_password != stored_password:
            record["password"] = secured_password
            migrated = True

        if migrated:
            self.datastore.save()

        result = ServiceResult(
            True,
            f"Chào mừng {self._display_name(role, record, normalized_username)}!",
            username=self._account_username(role, record, normalized_username),
            display_name=self._display_name(role, record, normalized_username),
            role=role,
        )

        write_activity_log(
            action="LOGIN",
            actor=normalized_username,
            role=role,
            status="SUCCESS",
            detail="Đăng nhập thành công.",
            datastore=self.datastore,
        )
        return result

    def register_user(
        self,
        username: str,
        password: str,
        fullname: str,
        phone: str,
    ) -> ServiceResult:
        """
        Mục đích:
            Thực hiện xử lý cho hàm `register_user` (register user).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            username: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            password: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            fullname: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            phone: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Giá trị theo khai báo kiểu trả về của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        normalized_username = normalize_username(username)
        normalized_fullname = normalize_fullname(fullname)
        normalized_phone = normalize_phone(phone)

        if not normalized_username or not str(password or "").strip() or not normalized_fullname:
            return ServiceResult(False, "Vui lòng nhập đủ các trường bắt buộc!", level="warning")

        if not is_valid_username(normalized_username):
            return ServiceResult(
                False,
                "Tên đăng nhập phải dài 3-30 ký tự và chỉ gồm chữ, số, dấu chấm, gạch dưới hoặc gạch ngang.",
                level="warning",
            )

        if not is_valid_password(password):
            return ServiceResult(False, "Mật khẩu phải có ít nhất 3 ký tự.", level="warning")

        if not is_valid_fullname(normalized_fullname):
            return ServiceResult(False, "Họ và tên phải có ít nhất 3 ký tự.", level="warning")

        if not is_valid_phone(normalized_phone):
            return ServiceResult(
                False,
                "Số điện thoại phải có 10 số, bắt đầu bằng 0 và dùng đầu số di động Việt Nam hợp lệ.",
                level="warning",
            )

        self.datastore.load()
        users = getattr(self.datastore, "list_users", self.datastore.data.get("users", []))
        if self.datastore.find_user(normalized_username) or any(
            str(user.get("username", "")).lower() == normalized_username.lower()
            for user in users
        ):
            write_activity_log(
                action="REGISTER_USER",
                actor=normalized_username,
                role="user",
                status="FAILED",
                detail="Tên đăng nhập đã tồn tại.",
                datastore=self.datastore,
            )
            return ServiceResult(False, "Tên đăng nhập đã tồn tại!", level="error")

        self.datastore.data.setdefault("users", []).append(
            {
                "username": normalized_username,
                "password": prepare_password_for_storage(password),
                "fullname": normalized_fullname,
                "sdt": normalized_phone,
            }
        )
        self.datastore.save()

        write_activity_log(
            action="REGISTER_USER",
            actor=normalized_username,
            role="user",
            status="SUCCESS",
            detail="Tạo tài khoản khách hàng mới.",
            datastore=self.datastore,
        )
        return ServiceResult(
            True,
            "Đăng ký tài khoản thành công!",
            username=normalized_username,
            display_name=normalized_fullname,
            role="user",
        )

    def _resolve_account(self, role: str, username: str):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_resolve_account` ( resolve account).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            role: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            username: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        if role == "admin":
            admin = self.datastore.data.get("admin", {})
            return admin if str(username).lower() == str(admin.get("username", "")).lower() else None
        if role == "guide":
            account = self.datastore.find_hdv(username)
            if account:
                return account
            username_upper = str(username).upper()
            return next(
                (h for h in self.datastore.list_hdv if str(h.get("maHDV", "")).upper() == username_upper),
                None,
            )
        if role == "user":
            account = self.datastore.find_user(username)
            if account:
                return account
            username_lower = str(username).lower()
            return next(
                (u for u in self.datastore.list_users if str(u.get("username", "")).lower() == username_lower),
                None,
            )
        return None

    @staticmethod
    def _account_username(role: str, record: dict, fallback: str) -> str:
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_account_username` ( account username).
        Tham số:
            role: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            record: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            fallback: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Giá trị theo khai báo kiểu trả về của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        if role == "guide":
            return record.get("maHDV", fallback)
        if role == "user":
            return record.get("username", fallback)
        if role == "admin":
            return record.get("username", fallback)
        return fallback

    @staticmethod
    def _display_name(role: str, record: dict, fallback: str) -> str:
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_display_name` ( display name).
        Tham số:
            role: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            record: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            fallback: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Giá trị theo khai báo kiểu trả về của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        if role == "guide":
            return record.get("tenHDV", fallback)
        if role == "user":
            return record.get("fullname", fallback)
        if role == "admin":
            return record.get("fullname", fallback)
        return fallback
