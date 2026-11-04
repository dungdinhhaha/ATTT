# Hướng dẫn trình bày đề tài 27 (5–7 phút)

## Trước khi vào lớp

1. Mở PowerShell tại `D:\attt\de_tai_27`.
2. Nếu máy chưa cài thư viện Python, chạy `python -m pip install -r requirements.txt` khi có mạng.
3. Chạy `powershell -NoProfile -ExecutionPolicy Bypass -File .\tests\start_demo.ps1`.
4. Giữ cửa sổ PowerShell và trang `tests\results\demo.html` đang mở. Script khởi động hai API lab tại `127.0.0.1:8001` (trước khi sửa) và `127.0.0.1:8000` (sau khi sửa), gọi request thật tới cả hai, chạy 26 ca tự động rồi mở bảng kết quả.

Nếu muốn kiểm tra nhanh API đang chạy: mở `http://127.0.0.1:8000/accounts/acc-a`; kết quả 401 là **đúng** vì request chưa có token.

## Kịch bản nói và thao tác

**Phút 1 — Mục tiêu và ma trận quyền.** Mở `app/policy/permission_matrix.csv`. Nói: “Trước khi kiểm thử, nhóm xác định ai được gọi chức năng nào và trên tài nguyên nào. Alice chỉ được đọc tài khoản của Alice; nhân viên hỗ trợ chỉ đọc tài khoản gắn ticket; chức năng admin chỉ dành cho admin.”

**Phút 2 — Trước khi sửa.** Ở PowerShell, chỉ vào phần `TRUOC KHI SUA`: Alice đọc tài khoản Bob trả 200; nhân viên hỗ trợ gọi API admin trả 200; yêu cầu sửa hồ sơ kèm `role=admin` trả 200. Hai lần gửi cùng khóa giao dịch tạo hai mã khác nhau. Đây là minh chứng lỗi, không phải mục tiêu mong muốn.

**Phút 3 — Sau khi sửa.** Chỉ vào phần `SAU KHI SUA`: BOLA và BFLA trả 403, mass assignment trả 400. Hai lần gửi cùng khóa chỉ có một mã giao dịch. `X-Request-ID` của từng phản hồi giúp đối chiếu log; không in token ra màn hình.

**Phút 4 — Hồi quy.** Chỉ vào dòng `26/26 ca đạt`, sau đó mở `tests\results\demo.html` để thấy toàn bộ 26 tình huống và bảng before/after. Mở `tests\results\before_after.json` nếu thầy hỏi request/response đã khử bí mật và log từ chối.

**Phút 5 — Kết luận và giới hạn.** Nói: “Lab dùng API tự viết và dữ liệu giả theo đúng lựa chọn của đề bài. Kết quả 26/26 là các ca đã viết, không khẳng định không còn lỗi. OPA đã được xác minh riêng trong Docker. Số độ trễ chỉ đo ASGI trong cùng tiến trình. Rate limit dùng cửa sổ 60 giây nhưng trạng thái vẫn nằm trong một tiến trình; khi triển khai nhiều instance phải dùng kho đếm chung.”

## Về Docker trên máy này

Docker Compose và OPA đã chạy và được xác minh ngày 02/11/2026. Để trình bày OPA, chạy `docker compose up -d --build`, sau đó `python tests/verify_opa.py` và mở `tests/results/opa_runtime.json`: OPA trả `true` cho Alice đọc tài khoản mình, `false` cho tài khoản Bob; API trả 200/403 tương ứng, 403 có `opa_denied` và correlation ID. Dừng bằng `docker compose down` trước khi chạy script demo Python dùng cùng cổng 8000.

Để trình diễn thêm request trực tiếp trên API Docker, chạy `python tests/live_demo.py --mode fixed` sau khi Compose khởi động. Dừng bằng `docker compose down`.

## Tệp cần nộp

- `app/before.py`, `app/after.py`, `Dockerfile`, `compose.yaml`, `requirements.txt`: mã hai API và cấu hình lab.
- `app/policy/permission_matrix.csv`: ma trận quyền.
- `tests/demo.py`, `tests/live_demo.py`, `tests\results\junit.xml`: kiểm thử tự động.
- `tests\results\demo.html`, `tests\results\before_after.json`, `tests\results\REPORT.md`: kết quả, request/response đã khử bí mật, log có correlation ID.
- `docs\guides\LOGGING.md`, `docs\guides\RULES_OF_ENGAGEMENT.md`, `docs\guides\THREAT_MODEL.md`: ghi log, giới hạn an toàn và mô hình đe dọa.
