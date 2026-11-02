# Phạm vi kiểm thử

- Chỉ dùng MiniBank-Lab tại `127.0.0.1` hoặc qua ASGI trong tiến trình cục bộ.
- Mọi tài khoản, token và số dư đều là dữ liệu giả. Không dùng API, token, tài khoản hay IP của hệ thống thật.
- Dừng thử nghiệm nếu dịch vụ không còn chạy trong lab hoặc request được định tuyến ra ngoài máy.
- Giới hạn kiểm thử tải ở các ca trong `demo.py` (20 request song song, 100 request đo mẫu).
- Không gửi kết quả hoặc log lên dịch vụ bên ngoài. Trước khi chia sẻ, xem lại `results/` để bảo đảm không có dữ liệu thật.
