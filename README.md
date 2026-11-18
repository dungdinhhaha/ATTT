# Đề tài 27 — MiniBank API Lab

[![SadServers Level](https://img.shields.io/badge/SadServers-Master-FF6D00?style=for-the-badge&labelColor=FFC400&logo=kubernetes&logoColor=1A237E&logoSize=auto)](https://sadservers.com/u/DINH+TIEN+DUNG)

Đồ án kiểm thử phân quyền đối tượng, phân quyền chức năng và giới hạn lạm dụng API. Dự án sử dụng **API tự viết trong lab cô lập**, đúng một trong hai lựa chọn của đề bài. Dữ liệu, tài khoản và token đều giả.

Hai phiên bản có mã riêng: `app/before.py` (cố ý có lỗi để kiểm thử) và `app/after.py` (đã bổ sung kiểm soát). Chạy đồng thời để so sánh: `python -m uvicorn app.before:app --port 8001` và `python -m uvicorn app.after:app --port 8000`.

## Chạy demo và xem kết quả

Để trình bày trực tiếp trước lớp, xem `docs/guides/HUONG_DAN_DEMO.md` và chạy `tests/start_demo.ps1`. Script mở hai API lab, gửi request thật tới bản trước/sau, chạy 26 ca hồi quy và mở bảng kết quả.

Muốn demo giao diện qua Burp và chạy test chỉ bằng Docker, chạy `powershell -NoProfile -ExecutionPolicy Bypass -File .\tests\start_web_demo.ps1`. Docker Compose chạy bản cũ ở cổng 8001, bản mới ở cổng 8000 cùng OPA; container kiểm thử chạy 26 ca và xác minh OPA. Mở hai trang `/demo` bằng Burp Browser và bảng `tests/results/demo.html`. Hướng dẫn ở `docs/guides/HUONG_DAN_WEB_DEMO.md`.

Muốn học cách tự viết hoặc mở rộng bộ test hồi quy, xem `docs/guides/HUONG_DAN_VIET_TEST_HOI_QUY.md` (ma trận quyền → request → assertion → chạy trước/sau → đọc kết quả).

Yêu cầu Python 3.12. Trong thư mục này:

```powershell
python -m pip install -r requirements.txt
python tests/demo.py
```

Mở `tests/results/demo.html` để xem bảng trước/sau. `tests/results/before_after.json` chứa kết quả chi tiết, trạng thái dữ liệu và log có correlation ID. Mỗi lần chạy demo tạo trạng thái mới nên có thể chạy lại.

## Chạy API bằng Docker

```powershell
docker compose up -d --build
python tests/verify_opa.py
```

Hai API chỉ bind `127.0.0.1`: bản trước sửa ở cổng 8001 và bản sau sửa có OPA ở cổng 8000. Lệnh xác minh OPA lưu quyết định trực tiếp và phản hồi API đã khử token vào `tests/results/opa_runtime.json`. Dừng bằng `docker compose down`.

## Cấu trúc minh chứng

- `app/before.py`, `app/after.py`: hai API độc lập; `app/api.py` chỉ giữ tương thích với lệnh cũ. Ma trận quyền và Rego ở `app/policy/`.
- `tests/`: bộ Python, demo trực tiếp, Postman/Newman và kết quả.
- `docs/guides/`: hướng dẫn demo, logging, mô hình đe dọa và quy tắc an toàn.
- `docs/evidence/Yeu_cau_va_minh_chung.xlsx`: đối chiếu từng yêu cầu đề bài với phần đã làm, cách tái hiện và minh chứng.
- `docs/reports/THESIS/`: báo cáo Word/PDF.
- `AI_CONTEXT.md`: bối cảnh để AI hỗ trợ nhóm đúng theo repo.

## Giới hạn trung thực

Đây là lab minh họa với dữ liệu trong bộ nhớ và JWT HS256 ký bằng khóa **giả, chỉ dùng trong lab**. OPA đã được xác minh trên Compose qua `tests/verify_opa.py`; bằng chứng nằm trong `tests/results/opa_runtime.json`. Rate limit dùng cửa sổ 60 giây theo địa chỉ kết nối và tài khoản, nhưng trạng thái vẫn chỉ nằm trong một tiến trình. Keycloak, crAPI và ZAP chưa được triển khai. Số đo ASGI cùng tiến trình là phép đo mẫu để so sánh lab, không suy ra hiệu năng production. Kết quả chạy thực tế nằm trong `tests/results/`.

