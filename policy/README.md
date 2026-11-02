# Policy phân quyền: trước và sau khi sửa

Tài liệu này là mục lục của thư mục policy. Mở theo thứ tự: `before/authorization.rego` để xem policy lỗi minh họa, `after/minibank.rego` để xem policy OPA sau khi sửa. Policy `before` chỉ dùng để học và đối chiếu, không dùng cho hệ thống thật.

## Nguyên tắc chung

Token hợp lệ chỉ xác nhận danh tính và tính toàn vẹn của claims. API vẫn phải xét hành động, đối tượng, quan hệ sở hữu, ticket, scope, role, MFA và điều kiện nghiệp vụ. Quyết định owner/ticket phải dựa vào dữ liệu do server truy xuất, không tin thuộc tính do client tự gửi.

## So sánh

| Tình huống | Policy trước sửa (vấn đề) | Policy sau sửa (điều kiện cho phép) |
|---|---|---|
| Đọc tài khoản | Chỉ cần token hợp lệ; không so owner | `subject == owner` |
| Support đọc tài khoản | Chỉ cần token; bỏ qua ticket | `role == support` và server xác nhận có ticket |
| Gọi chức năng admin | Route có thể chỉ kiểm token/scope | Role admin; với đổi role cần MFA và không tự đổi |
| Sửa hồ sơ | Nhận mọi trường client gửi | Chỉ chủ hồ sơ; schema chỉ nhận `full_name`, `phone` |
| Tạo chuyển khoản | Không ràng buộc chủ tài khoản nguồn | `subject == owner` của tài khoản nguồn |
| Token | Có thể bỏ qua một số claims | Kiểm chữ ký, thuật toán cho phép, issuer, audience, expiry, scope |
| Gửi lặp / lạm dụng | Có nguy cơ ghi lặp hoặc né ngưỡng | Idempotency, kiểm tra hash nội dung, khóa nguyên tử, hạn mức cộng dồn, rate limit |

## Pseudocode dễ đọc

### Trước sửa

```text
allow request nếu token được chấp nhận
không kiểm tra chủ tài khoản, ticket hoặc role trên mọi route
nhận trường ghi từ client
mỗi lần retry có thể tạo giao dịch mới
```

### Sau sửa

```text
1. Xác minh chữ ký JWT, iss, aud, exp và scope.
2. Xác định chủ thể từ token đã xác minh.
3. Đọc owner/ticket/role từ dữ liệu phía server.
4. Đánh giá policy theo action và resource.
5. Kiểm tra schema và nghiệp vụ trước khi ghi.
6. Dùng idempotency để retry không nhân đôi giao dịch.
7. Ghi quyết định cùng correlation ID, không ghi token.
```

## Policy OPA hiện hành

`after/minibank.rego` đặc tả sáu quyết định: `account_read`, `support_read`, `admin_list`, `admin_role_write`, `profile_write`, `transfer_create`. Mặc định `allow := false`; chỉ điều kiện khớp mới cho phép. API gửi subject, role, MFA và dữ kiện tài nguyên do server lấy tới OPA. Nếu OPA không trả `result: true` hoặc không phản hồi, API từ chối khi đã cấu hình `OPA_URL`.

Các kiểm tra token, schema, rate limit, idempotency và hạn mức vẫn nằm trong API, không nằm toàn bộ trong OPA. Vì vậy cần đọc cả `app.py`, `after/minibank.rego` và ma trận quyền để hiểu đầy đủ lớp bảo vệ.

## Trạng thái xác minh

Policy Rego và cấu hình Compose đã có trong repo; Docker Engine trên máy chưa chạy được ở lần kiểm tra gần nhất. Không xem đây là bằng chứng OPA runtime đã được kiểm nghiệm. Bộ Python 23 ca kiểm tra policy trong ứng dụng, không gọi OPA khi `OPA_URL` chưa đặt.

