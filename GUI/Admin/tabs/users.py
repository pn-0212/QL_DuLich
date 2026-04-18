from __future__ import annotations


def render(app):
    """
    Mục đích:
        Dựng tab quản lý khách hàng.
    Tham số:
        app: Ngữ cảnh ứng dụng admin hiện tại.
    Giá trị trả về:
        Kết quả trả về từ `admin.admin_user_tab`.
    Tác dụng phụ:
        Cập nhật danh sách user và các form thao tác liên quan.
    Lưu ý nghiệp vụ:
        Hàm chỉ ủy quyền, không thay đổi rule quản lý user.
    """
    from GUI.Admin import Admin as admin

    return admin.admin_user_tab(app)
