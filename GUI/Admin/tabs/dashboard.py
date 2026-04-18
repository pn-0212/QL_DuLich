from __future__ import annotations


def render(app):
    """
    Mục đích:
        Dựng tab tổng quan dashboard cho Admin.
    Tham số:
        app: Ngữ cảnh ứng dụng admin hiện tại.
    Giá trị trả về:
        Kết quả trả về từ `admin.dashboard_tab`.
    Tác dụng phụ:
        Cập nhật vùng nội dung dashboard.
    Lưu ý nghiệp vụ:
        Hàm bridge để module tab không phụ thuộc trực tiếp vào routing chính.
    """
    from GUI.Admin import Admin as admin

    return admin.dashboard_tab(app)
