# Policy sau khi sửa

`minibank.rego` là policy OPA hiện được Compose mount vào dịch vụ OPA. Mặc định từ chối; từng hành động chỉ được phép khi đủ điều kiện cụ thể. API phải cung cấp `subject`, `role`, `mfa` và thuộc tính tài nguyên được truy xuất từ phía server.

Các kiểm tra schema, JWT, rate limit, idempotency và hạn mức giao dịch vẫn được thực hiện trong API. Không đưa dữ liệu do client tự khai là owner/ticket vào quyết định policy.
