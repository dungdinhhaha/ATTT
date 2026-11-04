# Policy trước khi sửa

`authorization.rego` là policy cố ý lỏng để minh họa lỗi: nó chỉ yêu cầu có subject, không ràng buộc hành động, role, owner, ticket hay target. Vì vậy user đã xác thực có thể được cho phép truy cập tài nguyên/chức năng không thuộc quyền.

Trong demo, `app/before.py` mô phỏng tình trạng thiếu kiểm soát. Compose không nạp policy Rego trước sửa; tệp này là đặc tả minh họa để đối chiếu với bản sau. Không dùng policy này ngoài lab.
