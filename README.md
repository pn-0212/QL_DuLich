# Tour Management System (Tkinter) - phiên bản nâng cấp kiến trúc

Ứng dụng desktop quản lý tour du lịch với 3 vai trò:
- `admin`
- `khách hàng`
- `hướng dẫn viên`

Phiên bản này đã được tái cấu trúc để tăng độ an toàn, khả năng bảo trì và khả năng kiểm thử.

## 1) Điểm nâng cấp chính

- Tách lớp lưu trữ dùng chung về **một nguồn sự thật**: `core/datastore.py`.
- Chuyển persistence chính từ JSON sang **SQLite** (`travel_management.db`).
- Có cơ chế **migration tự động** từ JSON cũ sang SQLite khi chạy lần đầu.
- Nâng bảo mật mật khẩu từ SHA-256/plain sang **bcrypt**.
- Hỗ trợ xác thực dữ liệu cũ và **migrate hash cũ sau đăng nhập thành công**.
- Bổ sung test cho `security`, `auth`, `business rules`, `persistence`.
- Bổ sung tách module theo tab/feature cho `Admin`, `Khach`, `HuongDV`.

## 2) Kiến trúc hiện tại

```text
Tour-management/
├─ main.py
├─ requirements.txt
├─ core/
│  ├─ auth.py
│  ├─ security.py
│  ├─ datastore.py          # Nguồn sự thật persistence + migration JSON -> SQLite
│  ├─ booking_service.py
│  ├─ system_rules.py
│  ├─ validation.py
│  └─ ...
├─ GUI/
│  ├─ Admin/
│  │  ├─ Admin.py
│  │  └─ tabs/
│  ├─ Khach/
│  │  ├─ user.py
│  │  └─ features/
│  ├─ HuongDV/
│  │  ├─ Guide.py
│  │  └─ features/
│  └─ Login/login.py
└─ tests/
   ├─ test_security.py
   ├─ test_persistence_sqlite.py
   ├─ test_auth_and_booking_rules.py
   ├─ test_smoke_services.py
   └─ test_role_based_integration.py
```

## 3) Cơ chế dữ liệu

### 3.1 SQLite là nguồn chính
- File DB mặc định: `GUI/Admin/data/travel_management.db`.
- `DataStore` trong 3 module GUI đều dùng chung lớp `SQLiteDataStore`.

### 3.2 Migration JSON -> SQLite
Khi `travel_management.db` chưa tồn tại hoặc chưa khởi tạo:
1. Đọc dữ liệu legacy từ:
   - `GUI/Admin/data/vietnam_travel_data.json`
   - `GUI/Admin/data/vietnam_travel_reviews.json`
   - `GUI/Admin/data/vietnam_travel_notifications.json`
2. Chuẩn hóa nghiệp vụ qua `core/system_rules.py`.
3. Ghi vào SQLite.

Sau migration, runtime không còn phụ thuộc JSON làm nguồn chính.

## 4) Bảo mật xác thực

- Hash mới: `bcrypt`.
- Tương thích ngược:
  - Nếu dữ liệu cũ là SHA-256 hoặc plain text, hệ thống vẫn xác thực được.
  - Khi đăng nhập đúng, mật khẩu sẽ được nâng cấp lên bcrypt.

## 5) Cài đặt và chạy

### 5.1 Yêu cầu
- Python 3.11+

### 5.2 Cài thư viện
```bash
pip install -r requirements.txt
```

### 5.3 Chạy ứng dụng
```bash
python main.py
```

## 6) Chạy kiểm thử

```bash
pytest -q
```

Các nhóm test hiện có:
- `security`: hash/verify/migrate password.
- `auth`: đăng nhập và migrate hash legacy.
- `business rules`: giới hạn chỗ booking.
- `persistence`: migration JSON -> SQLite và khả năng hoạt động độc lập JSON.
- `integration`: flow role-based chính (admin tạo tour -> user booking -> guide theo dõi -> admin xử lý hoàn).

## 7) Build executable (tùy chọn)

```bash
pip install pyinstaller
pyinstaller --onefile --windowed main.py
```

## 8) Ưu điểm kỹ thuật nổi bật

- Kiến trúc dễ bảo trì hơn nhờ giảm trùng lặp DataStore.
- Dữ liệu bền hơn nhờ SQLite thay cho file JSON ghi đè liên tục.
- Auth an toàn hơn nhờ bcrypt + chiến lược migrate thực tế.
- Có bằng chứng kỹ thuật qua test tự động.

## 9) Hạn chế hiện tại và hướng phát triển

Hạn chế:
- GUI vẫn còn file lớn (đặc biệt module Admin/User/Guide).
- Chưa tách triệt để UI layer thành các view/component nhỏ độc lập.
- Chưa có test end-to-end cho Tkinter UI.

Hướng phát triển:
1. Tách tiếp GUI theo từng màn hình/chức năng.
2. Chuẩn hóa service/repository cho toàn bộ luồng CRUD.
3. Thêm smoke test UI và pipeline CI chạy test tự động.
4. Bổ sung đóng gói release script cho Windows.
