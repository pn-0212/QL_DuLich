from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module


@dataclass(frozen=True)
class AdminTabDef:
    """Mô tả metadata của một tab trong màn quản trị Admin."""

    key: str
    title: str
    subtitle: str
    icon: str
    module_name: str


TAB_DEFINITIONS: tuple[AdminTabDef, ...] = (
    AdminTabDef(
        key="dashboard",
        title="Tổng quan Dashboard",
        subtitle="Theo dõi nhanh doanh thu, số tour, HDV và booking trong hệ thống.",
        icon="",
        module_name="dashboard",
    ),
    AdminTabDef(
        key="hdv",
        title="Quản lý hướng dẫn viên",
        subtitle="Quản trị hồ sơ nhân sự, trạng thái và thông tin điều phối HDV.",
        icon="",
        module_name="hdv",
    ),
    AdminTabDef(
        key="users",
        title="Quản lý khách hàng",
        subtitle="Theo dõi tài khoản khách, lịch sử đặt chỗ và thông tin liên hệ.",
        icon="",
        module_name="users",
    ),
    AdminTabDef(
        key="tours",
        title="Quản lý tour",
        subtitle="Điều phối lịch trình, trạng thái tour và hướng dẫn viên phụ trách.",
        icon="",
        module_name="tours",
    ),
    AdminTabDef(
        key="bookings",
        title="Quản lý booking",
        subtitle="Kiểm soát booking, thanh toán và danh sách khách theo tour.",
        icon="",
        module_name="bookings",
    ),
    AdminTabDef(
        key="vouchers",
        title="Mã giảm giá",
        subtitle="Quản lý voucher, chương trình ưu đãi và điều kiện áp dụng.",
        icon="",
        module_name="vouchers",
    ),
    AdminTabDef(
        key="report",
        title="Báo cáo tổng hợp",
        subtitle="Xem nhanh báo cáo doanh thu và tổng hợp booking theo tour.",
        icon="",
        module_name="report",
    ),
    AdminTabDef(
        key="feedback",
        title="Đánh giá & thông báo",
        subtitle="Tổng hợp phản hồi khách hàng và gửi thông báo vận hành cho HDV.",
        icon="",
        module_name="feedback",
    ),
)


def get_admin_tab_definitions() -> tuple[AdminTabDef, ...]:
    """
    Mục đích:
        Trả về danh sách định nghĩa tab chuẩn cho phân hệ Admin.
    Tham số:
        Không có.
    Giá trị trả về:
        Tuple bất biến chứa metadata tất cả tab.
    Tác dụng phụ:
        Không có.
    Lưu ý nghiệp vụ:
        Thứ tự tuple quyết định thứ tự tab hiển thị trên thanh điều hướng.
    """
    return TAB_DEFINITIONS


def get_admin_tab_handler(tab_key: str):
    """
    Mục đích:
        Resolve hàm `render` tương ứng với mã tab.
    Tham số:
        tab_key: Mã tab được chọn từ giao diện.
    Giá trị trả về:
        Hàm handler `render` của module tab tương ứng.
    Tác dụng phụ:
        Import động module tab khi được gọi.
    Lưu ý nghiệp vụ:
        Nếu mã tab không hợp lệ, hệ thống fallback về tab đầu tiên.
    """
    normalized_key = str(tab_key or "").strip().lower()
    tab_def = next((item for item in TAB_DEFINITIONS if item.key == normalized_key), TAB_DEFINITIONS[0])
    module = import_module(f"GUI.Admin.tabs.{tab_def.module_name}")
    return getattr(module, "render")
