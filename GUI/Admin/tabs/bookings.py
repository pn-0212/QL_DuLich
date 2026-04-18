from __future__ import annotations


def render(app):
    """
    Mục đích:
        Dựng tab quản lý booking của phân hệ Admin.
    Tham số:
        app: Ngữ cảnh ứng dụng admin hiện tại.
    Giá trị trả về:
        Kết quả trả về từ `admin.admin_booking_tab`.
    Tác dụng phụ:
        Cập nhật vùng hiển thị tab booking.
    Lưu ý nghiệp vụ:
        Hàm chỉ đóng vai trò cầu nối để giữ kiến trúc tab tách module.
    """
    from GUI.Admin import Admin as admin

    return admin.admin_booking_tab(app)
