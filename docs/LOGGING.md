# Hướng dẫn ghi log

Mỗi request trả `X-Request-ID` và tạo một bản ghi gồm: `request_id`, `subject` giả, HTTP method, route mẫu, `decision`, `policy_id`, status và thời gian xử lý. Khi điều tra, lấy ID trong phản hồi để tìm đúng bản ghi.

Không ghi `Authorization`, JWT, mật khẩu, body, số tài khoản thật, email hoặc thông tin thanh toán. `results/before_after.json` chỉ chứa request/response đã lược bỏ token và dữ liệu giả. Với triển khai thật, dùng logger tập trung có quyền truy cập hạn chế và thời hạn lưu giữ do tổ chức quy định.

Phép kiểm trong demo xác nhận token mẫu không xuất hiện trong log và request ID khớp. Đây là kiểm tra mẫu, chưa thay thế được quét toàn bộ luồng log của hệ thống thật.
