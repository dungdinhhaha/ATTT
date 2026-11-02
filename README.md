# Đề tài 27 — MiniBank API Lab

Đồ án kiểm thử phân quyền đối tượng, phân quyền chức năng và giới hạn lạm dụng API. Dự án sử dụng **API tự viết trong lab cô lập**, đúng một trong hai lựa chọn của đề bài. Dữ liệu, tài khoản và token đều giả.

## Chạy demo và xem kết quả

Để trình bày trực tiếp trước lớp, xem `HUONG_DAN_DEMO.md` và chạy `start_demo.ps1`. Script mở hai API lab, gửi request thật tới bản trước/sau, chạy 23 ca hồi quy và mở bảng kết quả.

Yêu cầu Python 3.12. Trong thư mục này:

```powershell
python -m pip install -r requirements.txt
python demo.py
```

Mở `results/demo.html` để xem bảng trước/sau. `results/before_after.json` chứa kết quả chi tiết, trạng thái dữ liệu và log có correlation ID. Mỗi lần chạy demo tạo trạng thái mới nên có thể chạy lại.

## Chạy API bằng Docker

```powershell
docker compose up --build
```

API chỉ bind `127.0.0.1:8000`; mặc định là bản đã sửa. Để tái hiện v1 trong lab, đặt `LAB_MODE=before` trước khi chạy Compose. Dừng bằng `docker compose down`.

## Cấu trúc minh chứng

- `app.py`: mã API v1/v2, middleware, JWT, policy, giới hạn và log.
- `permission_matrix.csv`: actor–method–route–điều kiện–quyết định–ca demo.
- `demo.py`: bộ kiểm thử tự động và tạo kết quả thực tế.
- `results/`: bảng trước/sau, request/response đã khử token, log mẫu và trang demo.
- `docs/THREAT_MODEL.md`: DFD, ranh giới tin cậy, 13 mối đe dọa STRIDE.
- `docs/LOGGING.md`: hướng dẫn ghi log.
- `docs/RULES_OF_ENGAGEMENT.md`: phạm vi an toàn.
- `policy/after/minibank.rego` và `policy/before/authorization.rego`, `docs/OPA_NEWMAN.md`: policy OPA và cách chạy Newman.

## Giới hạn trung thực

Đây là lab minh họa với dữ liệu trong bộ nhớ và JWT HS256 ký bằng khóa **giả, chỉ dùng trong lab**. Các công nghệ Keycloak, OPA, crAPI và ZAP là gợi ý hoặc phần mở rộng, chưa được triển khai trong bản này. Số đo ASGI cùng tiến trình là phép đo mẫu để so sánh lab, không suy ra hiệu năng production. Kết quả chạy thực tế nằm trong `results/`, không được thay bằng mục tiêu dự kiến trong kế hoạch.

