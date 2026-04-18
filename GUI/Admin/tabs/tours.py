from __future__ import annotations


def render(app):
    """
    Mục đích:
        Dựng tab quản lý tour của admin.
    Tham số:
        app: Ngữ cảnh ứng dụng admin hiện tại.
    Giá trị trả về:
        Kết quả trả về từ `admin.admin_tour_tab`.
    Tác dụng phụ:
        Cập nhật danh sách và form thao tác tour trên UI.
    Lưu ý nghiệp vụ:
        Logic nghiệp vụ tour vẫn nằm trong module admin chính và tầng core.
    """
    from GUI.Admin import Admin as admin

    return admin.admin_tour_tab(app)
