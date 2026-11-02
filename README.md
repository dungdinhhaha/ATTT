# Đề tài 27 — MiniBank API Lab

Đồ án kiểm thử phân quyền đối tượng, phân quyền chức năng và giới hạn lạm dụng API. Dự án sử dụng **API tự viết trong lab cô lập**, đúng một trong hai lựa chọn của đề bài. Dữ liệu, tài khoản và token đều giả.

## Chạy demo và xem kết quả

Để trình bày trực tiếp trước lớp, xem `docs/guides/HUONG_DAN_DEMO.md` và chạy `tests/start_demo.ps1`. Script mở hai API lab, gửi request thật tới bản trước/sau, chạy 23 ca hồi quy và mở bảng kết quả.

Yêu cầu Python 3.12. Trong thư mục này:

```powershell
python -m pip install -r requirements.txt
python tests/demo.py
```

Mở `tests/results/demo.html` để xem bảng trước/sau. `tests/results/before_after.json` chứa kết quả chi tiết, trạng thái dữ liệu và log có correlation ID. Mỗi lần chạy demo tạo trạng thái mới nên có thể chạy lại.

## Chạy API bằng Docker

```powershell
docker compose up --build
```

API chỉ bind `127.0.0.1:8000`; mặc định là bản đã sửa. Để tái hiện v1 trong lab, đặt `LAB_MODE=before` trước khi chạy Compose. Dừng bằng `docker compose down`.

## Cấu trúc minh chứng

- `app/`: API, ma trận quyền và policy trước/sau sửa.
- `tests/`: bộ Python, demo trực tiếp, Postman/Newman và kết quả.
- `docs/guides/`: hướng dẫn demo, logging, mô hình đe dọa và quy tắc an toàn.
- `docs/planning/`: workbook kế hoạch nhóm.
- `docs/reports/THESIS/`: báo cáo Word/PDF.
- `AI_CONTEXT.md`: bối cảnh để AI hỗ trợ nhóm đúng theo repo.

## Giới hạn trung thực

Đây là lab minh họa với dữ liệu trong bộ nhớ và JWT HS256 ký bằng khóa **giả, chỉ dùng trong lab**. Policy OPA có mã và cấu hình Compose nhưng chưa có kết quả runtime được xác minh trên máy. Keycloak, crAPI và ZAP chưa được triển khai. Số đo ASGI cùng tiến trình là phép đo mẫu để so sánh lab, không suy ra hiệu năng production. Kết quả chạy thực tế nằm trong `tests/results/`, không được thay bằng mục tiêu dự kiến trong kế hoạch.

