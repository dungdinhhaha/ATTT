# Hướng dẫn trình bày đề tài 27 (5–7 phút)

## Trước khi vào lớp

1. Mở PowerShell tại `D:\attt\de_tai_27`.
2. Nếu máy chưa cài thư viện Python, chạy `python -m pip install -r requirements.txt` khi có mạng.
3. Chạy `powershell -NoProfile -ExecutionPolicy Bypass -File .\start_demo.ps1`.
4. Giữ cửa sổ PowerShell và trang `results\demo.html` đang mở. Script khởi động hai API lab tại `127.0.0.1:8001` (trước khi sửa) và `127.0.0.1:8000` (sau khi sửa), gọi request thật tới cả hai, chạy 23 ca tự động rồi mở bảng kết quả.

Nếu muốn kiểm tra nhanh API đang chạy: mở `http://127.0.0.1:8000/accounts/acc-a`; kết quả 401 là **đúng** vì request chưa có token.

## Kịch bản nói và thao tác

**Phút 1 — Mục tiêu và ma trận quyền.** Mở `permission_matrix.csv`. Nói: “Trước khi kiểm thử, nhóm xác định ai được gọi chức năng nào và trên tài nguyên nào. Alice chỉ được đọc tài khoản của Alice; nhân viên hỗ trợ chỉ đọc tài khoản gắn ticket; chức năng admin chỉ dành cho admin.”

**Phút 2 — Trước khi sửa.** Ở PowerShell, chỉ vào phần `TRUOC KHI SUA`: Alice đọc tài khoản Bob trả 200; nhân viên hỗ trợ gọi API admin trả 200; yêu cầu sửa hồ sơ kèm `role=admin` trả 200. Hai lần gửi cùng khóa giao dịch tạo hai mã khác nhau. Đây là minh chứng lỗi, không phải mục tiêu mong muốn.

**Phút 3 — Sau khi sửa.** Chỉ vào phần `SAU KHI SUA`: BOLA và BFLA trả 403, mass assignment trả 400. Hai lần gửi cùng khóa chỉ có một mã giao dịch. `X-Request-ID` của từng phản hồi giúp đối chiếu log; không in token ra màn hình.

**Phút 4 — Hồi quy.** Chỉ vào dòng `23/23 ca đạt`, sau đó mở `results\demo.html` để thấy toàn bộ 23 tình huống và bảng before/after. Mở `results\before_after.json` nếu thầy hỏi request/response đã khử bí mật và log từ chối.

**Phút 5 — Kết luận và giới hạn.** Nói: “Lab dùng API tự viết và dữ liệu giả theo đúng lựa chọn của đề bài. Kết quả 23/23 là các ca đã viết, không khẳng định không còn lỗi. Số độ trễ chỉ đo ASGI trong cùng tiến trình. Rate limit đang dùng bộ nhớ tiến trình; khi triển khai nhiều instance phải dùng kho đếm chung. Không dùng API hoặc token thật.”

## Về Docker trên máy này

Docker CLI và Docker Desktop **đã cài**, nhưng lần kiểm tra ngày 02/11/2026 Docker Engine chưa chạy. `docker version` chỉ trả thông tin Client và báo không tìm thấy `dockerDesktopLinuxEngine`. Log Docker Desktop ghi lỗi mở `AppData\Local\docker-secrets-engine\engine.sock`; thử đổi tên tệp để giữ bản sao cũng bị Windows từ chối. Vì vậy hiện tại **không trình bày rằng container đã chạy**. Script ở trên chạy cùng API lab bằng Python và đã được kiểm tra thực tế.

Khi Docker Desktop hoạt động trở lại, có thể chứng minh cấu hình container bằng `docker compose up --build` tại thư mục này. API sẽ chỉ lắng nghe ở `127.0.0.1:8000`; sau đó chạy `python live_demo.py --mode fixed`. Dừng bằng `docker compose down`.

## Tệp cần nộp

- `app.py`, `Dockerfile`, `compose.yaml`, `requirements.txt`: mã và cấu hình lab.
- `permission_matrix.csv`: ma trận quyền.
- `demo.py`, `live_demo.py`, `results\junit.xml`: kiểm thử tự động.
- `results\demo.html`, `results\before_after.json`, `results\REPORT.md`: kết quả, request/response đã khử bí mật, log có correlation ID.
- `docs\LOGGING.md`, `docs\RULES_OF_ENGAGEMENT.md`, `docs\THREAT_MODEL.md`: ghi log, giới hạn an toàn và mô hình đe dọa.
