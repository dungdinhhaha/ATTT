# Báo cáo thực nghiệm — Đề tài 27

## Phạm vi

MiniBank-Lab là API tự viết, dữ liệu và token giả, chạy cục bộ. Hai chế độ v1/v2 dùng cùng mã nguồn và dữ liệu khởi tạo. Không kết nối API thật.

## Cơ sở lý thuyết

- Xác thực trả lời ai đang gọi; phân quyền chức năng trả lời được gọi route nào; phân quyền đối tượng trả lời được thao tác trên bản ghi nào.
- JWT đã ký chỉ xác nhận nội dung token không bị sửa theo khóa ký. API vẫn phải kiểm issuer, audience, thời hạn, scope và quan hệ của người dùng với tài nguyên.
- BOLA liên quan tới owner hoặc ticket; BFLA liên quan tới chức năng admin; mass assignment xảy ra khi client đặt trường mà server phải tự quyết định.
- Rate limit kiểm soát tần suất; idempotency bảo đảm gửi lại cùng lệnh không nhân đôi giao dịch; kiểm tra hạn mức phải cộng dồn theo luồng nghiệp vụ.

## Kết quả từ lần chạy này

Bản v2 đạt **26/26** ca. Các ca này là mẫu kiểm tra đã triển khai, không phải tuyên bố phủ mọi route hay mọi biến thể tấn công.

| Ca kiểm thử | HTTP v1 | HTTP v2 | v2 đạt? |
|---|---:|---:|---|
| BOLA support ngoài ticket | 200 | 403 | Có |
| Support có ticket | 200 | 200 | Có |
| BOLA customer | 200 | 403 | Có |
| Customer hợp lệ | 200 | 200 | Có |
| Không có token | 401 | 401 | Có |
| Sửa hồ sơ hợp lệ | 200 | 200 | Có |
| BFLA support nâng role | 200 | 403 | Có |
| Thiếu scope admin | 200 | 403 | Có |
| Admin hợp lệ | 200 | 200 | Có |
| Admin thiếu MFA | 200 | 403 | Có |
| Admin tự nâng quyền | 200 | 403 | Có |
| Mass assignment | 200 | 400 | Có |
| Chuyển từ tài khoản khác | 200 | 403 | Có |
| Gửi lặp giao dịch | 200 | 200 | Có |
| Gửi song song cùng key | 400 | 200 | Có |
| Cùng key khác nội dung | 200 | 409 | Có |
| Chia nhỏ vượt hạn mức | 200 | 403 | Có |
| Giới hạn đăng nhập | 401 | 429 | Có |
| Đăng nhập dưới ngưỡng | 401 | 401 | Có |
| Rate limit tách tài khoản | 401 | 401 | Có |
| Rate limit hết cửa sổ | 401 | 401 | Có |
| Giới hạn page size | 200 | 400 | Có |
| JWT sai audience | 200 | 401 | Có |
| JWT hết hạn | 200 | 401 | Có |
| Agent không được ghi | 200 | 403 | Có |
| Log có ID, không lộ token | 200 | 403 | Có |

## Đo độ trễ mẫu

p95 v1: 2.781 ms; p95 v2: 2.97 ms. Mỗi chế độ có 20 request làm nóng và 100 request đo, chạy qua ASGI trong cùng tiến trình.
Số này chỉ mô tả lần chạy trên máy lab; cần tải thật qua HTTP, nhiều lần lặp và phần cứng cố định để kết luận overhead triển khai.

## Minh chứng

- Mã lab: `app/api.py`, `compose.yaml`, `Dockerfile`.
- Ma trận quyền: `app/policy/permission_matrix.csv`.
- Bộ test tự động: `tests/demo.py`; báo cáo máy đọc: `tests/results/junit.xml`.
- Request/response đã bỏ token, trạng thái DB và log từ chối có correlation ID: `tests/results/before_after.json`.
- Đặc tả OpenAPI: `tests/results/openapi.json`.
- Hướng dẫn log và phạm vi đạo đức: `docs/guides/LOGGING.md`, `docs/guides/RULES_OF_ENGAGEMENT.md`.

## Giới hạn

Lab dùng dữ liệu trong bộ nhớ và issuer JWT giả; chưa tích hợp Keycloak, crAPI hoặc ZAP. OPA đã được xác minh riêng qua Compose, xem `tests/results/opa_runtime.json`; bộ ASGI này không bật OPA. Rate limit có cửa sổ 60 giây theo địa chỉ kết nối và tài khoản nhưng trạng thái chỉ nằm trong một tiến trình. Log chưa được đẩy tới kho append-only. JWT role có thể cũ sau khi đổi quyền; hành động admin đọc role hiện tại từ lab.
