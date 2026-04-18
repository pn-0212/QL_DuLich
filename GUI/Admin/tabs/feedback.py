from __future__ import annotations


def render(app):
    """
    Mục đích:
        Dựng tab đánh giá và thông báo vận hành.
    Tham số:
        app: Ngữ cảnh ứng dụng admin hiện tại.
    Giá trị trả về:
        Kết quả trả về từ `admin.admin_feedback_tab`.
    Tác dụng phụ:
        Cập nhật danh sách phản hồi/thông báo trong giao diện.
    Lưu ý nghiệp vụ:
        Hàm này không chứa logic nghiệp vụ, chỉ điều hướng tab.
    """
    from GUI.Admin import Admin as admin

    return admin.admin_feedback_tab(app)
