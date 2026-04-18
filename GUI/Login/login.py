import tkinter as tk

root = None


def set_root(external_root):
    """
    Mục đích:
        Gán tham chiếu cửa sổ gốc dùng chung cho module đăng nhập.
    Tham số:
        external_root: Đối tượng `tk.Tk` hoặc `tk.Toplevel` được cấp từ bên ngoài.
    Giá trị trả về:
        Không trả về giá trị.
    Tác dụng phụ:
        Cập nhật biến module `root`.
    Lưu ý nghiệp vụ:
        Cần gọi trước `show_role_selection` khi module được dùng độc lập.
    """
    global root
    root = external_root


def show_role_selection():
    """
    Mục đích:
        Dọn giao diện hiện tại và hiển thị lại màn chọn vai trò đăng nhập.
    Tham số:
        Không có.
    Giá trị trả về:
        Không trả về giá trị.
    Tác dụng phụ:
        Xóa toàn bộ widget cũ trong root và khởi tạo `TravelSystem`.
    Lưu ý nghiệp vụ:
        Hàm này là điểm vào chung khi cần quay về màn login ban đầu.
    """
    if root is None:
        raise RuntimeError("Login root chưa được khởi tạo")

    from main import TravelSystem

    for widget in root.winfo_children():
        widget.destroy()

    TravelSystem(root)


if __name__ == "__main__":
    root = tk.Tk()
    show_role_selection()
    root.mainloop()
