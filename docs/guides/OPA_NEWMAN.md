# Minh chứng OPA và Newman

## OPA

`app/policy/after/minibank.rego` đặc tả sáu quyết định phân quyền: đọc tài khoản của chủ sở hữu, đọc qua ticket hỗ trợ, xem danh sách admin, đổi vai trò, sửa hồ sơ cá nhân và tạo chuyển khoản từ tài khoản sở hữu. API gửi subject, role, MFA và thuộc tính tài nguyên do máy chủ xác định tới `POST /v1/data/minibank/authz/allow`. OPA trả `result: true` mới được phép tiếp tục. Khi `OPA_URL` đã cấu hình mà OPA không phản hồi hoặc không có kết quả, API từ chối theo nguyên tắc fail closed.

Compose gắn API và OPA vào mạng nội bộ `lab`, không công khai cổng OPA. Chạy `docker compose up --build` khi Docker Engine hoạt động. Kiểm tra bản đã sửa bằng `python tests/live_demo.py --mode fixed`. Chế độ Python chạy trực tiếp không đặt `OPA_URL` nên tiếp tục dùng policy trong ứng dụng; kết quả Python không được ghi là kết quả OPA.

## Newman

Hai collection `tests/postman/De_tai_27_BOLA_before.postman_collection.json` và `tests/postman/De_tai_27_BOLA_after.postman_collection.json` đã chạy bằng Newman, mỗi bộ 3/3 assertions đạt. Chạy lại sau khi đã bật API trên cổng 8001/8000:

```powershell
npx --yes newman run tests/postman/De_tai_27_BOLA_before.postman_collection.json --reporters cli,junit --reporter-junit-export tests/results/newman_bola_before.xml
npx --yes newman run tests/postman/De_tai_27_BOLA_after.postman_collection.json --reporters cli,junit --reporter-junit-export tests/results/newman_bola_after.xml
```

Hai collection này chỉ minh họa BOLA và truy cập hợp lệ. Bộ Python `tests/demo.py` bao phủ 23 tình huống với trạng thái lab mới cho từng ca. Không báo cáo Postman là bộ kiểm thử 23 ca.

