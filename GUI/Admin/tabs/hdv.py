from __future__ import annotations


def render(app):
    """
    Mục đích:
        Dựng tab quản lý hướng dẫn viên.
    Tham số:
        app: Ngữ cảnh ứng dụng admin hiện tại.
    Giá trị trả về:
        Kết quả trả về từ `admin.admin_hdv_tab`.
    Tác dụng phụ:
        Cập nhật danh sách/hồ sơ HDV trên giao diện.
    Lưu ý nghiệp vụ:
        Tách module tab để tránh file router chính phình to thêm.
    """
    from GUI.Admin import Admin as admin

    return admin.admin_hdv_tab(app)
