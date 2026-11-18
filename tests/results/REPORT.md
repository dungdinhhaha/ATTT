# Báo cáo thực nghiệm — Đề tài 27

## Phạm vi

MiniBank-Lab là API tự viết, dữ liệu và token giả, chạy cục bộ. Hai bản có mã riêng ở app/before.py và app/after.py, cùng dữ liệu khởi tạo để so sánh. Không kết nối API thật.

## Cơ sở lý thuyết

- Xác thực trả lời ai đang gọi; phân quyền chức năng trả lời được gọi route nào; phân quyền đối tượng trả lời được thao tác trên bản ghi nào.
- JWT đã ký chỉ xác nhận nội dung token không bị sửa theo khóa ký. API vẫn phải kiểm issuer, audience, thời hạn, scope và quan hệ của người dùng với tài nguyên.
- BOLA liên quan tới owner hoặc ticket; BFLA liên quan tới chức năng admin; mass assignment xảy ra khi client đặt trường mà server phải tự quyết định.
- Rate limit kiểm soát tần suất; idempotency bảo đảm gửi lại cùng lệnh không nhân đôi giao dịch; kiểm tra hạn mức phải cộng dồn theo luồng nghiệp vụ.

## Kết quả từ lần chạy này

Bản v2 đạt **26/26** ca. Các ca này là mẫu kiểm tra đã triển khai, không phải tuyên bố phủ mọi route hay mọi biến thể tấn công.

| Ca kiểm thử | HTTP v1 | HTTP v2 | Giao dịch ghi nhận v1/v2 | v2 đạt? |
|---|---:|---:|---:|---|
| BOLA support ngoài ticket | 200 | 403 | 0/0 | Có |
| Support có ticket | 200 | 200 | 0/0 | Có |
| BOLA customer | 200 | 403 | 0/0 | Có |
| Customer hợp lệ | 200 | 200 | 0/0 | Có |
| Không có token | 401 | 401 | 0/0 | Có |
| Sửa hồ sơ hợp lệ | 200 | 200 | 0/0 | Có |
| BFLA support nâng role | 200 | 403 | 0/0 | Có |
| Thiếu scope admin | 200 | 403 | 0/0 | Có |
| Admin hợp lệ | 200 | 200 | 0/0 | Có |
| Admin thiếu MFA | 200 | 403 | 0/0 | Có |
| Admin tự nâng quyền | 200 | 403 | 0/0 | Có |
| Mass assignment | 200 | 400 | 0/0 | Có |
| Chuyển từ tài khoản khác | 200 | 403 | 1/0 | Có |
| Gửi lặp giao dịch | 200 | 200 | 5/1 | Có |
| Gửi song song cùng key | 200 | 200 | 20/1 | Có |
| Cùng key khác nội dung | 200 | 409 | 2/1 | Có |
| Chia nhỏ vượt hạn mức | 200 | 403 | 4/3 | Có |
| Giới hạn đăng nhập | 401 | 429 | 0/0 | Có |
| Đăng nhập dưới ngưỡng | 401 | 401 | 0/0 | Có |
| Rate limit tách tài khoản | 401 | 401 | 0/0 | Có |
| Rate limit hết cửa sổ | 401 | 401 | 0/0 | Có |
| Giới hạn page size | 200 | 400 | 0/0 | Có |
| JWT sai audience | 200 | 401 | 0/0 | Có |
| JWT hết hạn | 200 | 401 | 0/0 | Có |
| Agent không được ghi | 200 | 403 | 1/0 | Có |
| Log có ID, không lộ token | 200 | 200 | 0/0 | Có |

## Thống kê theo nhóm

| Nhóm | Số ca | v1 đạt | v2 đạt |
|---|---:|---:|---:|
| Chặn đúng ca tấn công | 16 | 1 | 16 |
| Chống trùng giao dịch | 2 | 0 | 2 |
| Đường hợp lệ (kiểm tra hồi quy) | 4 | 3 | 4 |
| Cho phép đúng ở ngưỡng đăng nhập | 3 | 1 | 3 |
| Truy vết log | 1 | 1 | 1 |

## Đo độ trễ mẫu

p95 v1: 21.883 ms; p95 v2: 21.123 ms. Mỗi chế độ có 20 request làm nóng và 100 request đo, chạy qua ASGI trong cùng tiến trình.
Số này chỉ mô tả lần chạy trên máy lab; cần tải thật qua HTTP, nhiều lần lặp và phần cứng cố định để kết luận overhead triển khai.

## Minh chứng

- Mã lab: `app/before.py`, `app/after.py`, `compose.yaml`, `Dockerfile`.
- Ma trận quyền: `app/policy/permission_matrix.csv`.
- Bộ test tự động: `tests/demo.py`; báo cáo máy đọc: `tests/results/junit.xml`.
- Request/response đã bỏ token, trạng thái DB và log từ chối có correlation ID: `tests/results/before_after.json`.
- Đặc tả OpenAPI: `tests/results/openapi.json`.
- Log ứng dụng dạng JSON lines (không chứa token): `tests/results/app_log_before.jsonl`, `tests/results/app_log_after.jsonl`.
- Hướng dẫn log và phạm vi đạo đức: `docs/guides/LOGGING.md`, `docs/guides/RULES_OF_ENGAGEMENT.md`.

## Giới hạn

Lab dùng dữ liệu trong bộ nhớ và issuer JWT giả; chưa tích hợp Keycloak, crAPI hoặc ZAP. OPA đã được xác minh riêng qua Compose, xem `tests/results/opa_runtime.json`; bộ ASGI này không bật OPA. Rate limit có cửa sổ 60 giây theo địa chỉ kết nối và tài khoản nhưng trạng thái chỉ nằm trong một tiến trình. Log chưa được đẩy tới kho append-only. JWT role có thể cũ sau khi đổi quyền; hành động admin đọc role hiện tại từ lab.
