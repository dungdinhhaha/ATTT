# Hướng dẫn trình diễn web, Burp và kiểm thử hồi quy

Tài liệu này dùng cho MiniBank API Lab của đề tài 27. Tài khoản, token, số dư và giao dịch đều là dữ liệu giả. Chỉ thao tác với hai địa chỉ `127.0.0.1` của lab.

## 1. Bật toàn bộ lab

1. Mở **Docker Desktop**, chờ Docker Engine chạy, rồi mở **Burp Suite**.
2. Trong PowerShell chạy:

   ```powershell
   cd D:\attt\de_tai_27
   powershell -NoProfile -ExecutionPolicy Bypass -File .\tests\start_web_demo.ps1
   ```

3. Chờ dòng `v2: 26/26 ca đạt` và `OPA runtime verified`. Script bật API trước sửa, API sau sửa, OPA và chạy container kiểm thử. Kết quả được ghi vào `tests\results`.

| Mục đích | Địa chỉ hoặc tệp |
|---|---|
| Web/API trước sửa | `http://127.0.0.1:8001/demo` |
| Web/API sau sửa, có OPA | `http://127.0.0.1:8000/demo` |
| Bảng kết quả 26 ca | `tests\results\demo.html` |
| Bằng chứng OPA đang chạy | `tests\results\opa_runtime.json` |

Nếu đã thử chuyển khoản trước buổi trình bày, chạy `docker compose down` rồi chạy lại script để dữ liệu trong bộ nhớ trở về ban đầu; mỗi tài khoản khởi đầu với số dư 100.

## 2. Bắt request bằng Burp

1. Vào **Burp → Proxy → Intercept → Open Browser**. Dùng *Burp Browser* để mở cả hai URL trong bảng. Trình duyệt ngoài Burp có thể không đi qua proxy.
2. Đặt **Intercept off** để các nút hoạt động liên tục. Xem request và response ở **Proxy → HTTP history**; phân biệt bản cũ bằng cổng `8001`, bản mới bằng cổng `8000`.
3. Khi muốn chỉ request *trước khi gửi*, bật **Intercept on**, bấm nút tình huống trên web, cho lớp xem method, path, header và body, rồi bấm **Forward**. Chuyển về **Intercept off** sau đó; nếu để on, web sẽ tiếp tục chờ request khác.
4. Muốn sửa hoặc gửi lại request, nhấp phải nó trong HTTP history → **Send to Repeater**, chỉnh nội dung rồi bấm **Send**. Chỉ dùng với lab `127.0.0.1`.

Trang web có ba vùng: **chọn người dùng**, **chọn thao tác**, **quan sát kết quả**. Cột kết quả hiện HTTP status, mã giao dịch, số dư, `X-Request-ID` và JSON. Nút **Tạo phiên demo** cấp token giả. Token hiện trong Burp; nếu chụp ảnh hoặc chia sẻ request thì che giá trị `Authorization`.

## 3. Demo lỗi trước/sau

Với mỗi tình huống, làm ở `:8001` trước rồi làm lại ở `:8000`. **Trên mỗi trang**, chọn người dùng và bấm **Tạo phiên demo** trước khi thử. Không cần sao chép token giữa hai trang.

| Tình huống và nút trên web | Request trong Burp | Trước sửa `:8001` | Sau sửa `:8000` | Điều cần giải thích |
|---|---|---|---|---|
| **BOLA:** Alice → **Gửi request BOLA** | `GET /accounts/acc-b` | `200`, đọc được tài khoản Bob | `403` | Alice có token và scope đọc, nhưng `acc-b` thuộc Bob. Bản sửa kiểm tra owner qua OPA. |
| **BFLA:** Sam → **Gửi request BFLA** | `GET /admin/users` | `200` | `403` | Token lab của Sam có `admin:users` để tách lỗi scope khỏi lỗi vai trò. Sam vẫn là support; OPA từ chối chức năng admin. |
| **Gửi lặp:** Alice → nhập `10` → **1. Chuyển tiền** → **2. Gửi lại cùng khóa** | Hai `POST /transfers` cùng `Idempotency-Key` và body | Hai mã giao dịch; số dư `acc-a`: `100 → 90 → 80` | Cùng mã giao dịch; số dư `100 → 90 → 90` | Bản sửa trả lại kết quả cũ khi gửi lại cùng khóa, không trừ tiền lần hai. |

Ở ca gửi lặp, mở hai request `POST /transfers` trong Burp để chỉ ra **cùng `Idempotency-Key`**. Trên web, chỉ vùng **Lịch sử thao tác**, **Giao dịch** và **Số dư**. Nếu số dư ban đầu không phải 100, đặt lại container theo mục 1 trước khi nói các con số này.

Nếu còn thời gian, demo thêm hai ca:

- Alice → **Đọc tài khoản Alice**: `GET /accounts/acc-a` trả `200` ở cả hai bản. Đây là ca cho phép đúng.
- Alice → **Gửi request sửa role**: `PATCH /profile/alice` với body `role=admin` trả `200` trước sửa và `400` sau sửa. Bản sửa không cho client tự gán vai trò qua sửa hồ sơ.

## 4. Demo bộ kiểm thử hồi quy

Sau phần Burp, mở báo cáo được tạo ở bước khởi động:

```powershell
Invoke-Item .\tests\results\demo.html
```

Chỉ cột **HTTP v1**, **HTTP v2**, **Kết quả v2** và dòng **26/26 ca đạt**. Các ca bao gồm BOLA, BFLA, mass assignment, gửi lặp, JWT, rate limit, giới hạn dữ liệu và đường hợp lệ. Để chứng minh test tự động có thể chạy lại trong Docker mà vẫn giữ web đang mở:

```powershell
docker compose --profile tests run --rm --no-deps regression
```

Lệnh này cập nhật `tests\results\demo.html`, `before_after.json`, `junit.xml` và `opa_runtime.json`. Tải lại trang báo cáo sau khi chạy. Nếu bản sau có ca không đạt, container kiểm thử trả mã lỗi.

**Phân biệt hai minh chứng:** 26 ca chạy bằng HTTPX ASGI *trong container kiểm thử* trên mã hai phiên bản; chúng không đi qua Burp hoặc OPA sidecar. Bước `OPA runtime verified` gửi HTTP thật tới OPA và API sau sửa đang chạy trong Compose. Mở `opa_runtime.json` để xem Alice đọc tài khoản mình `200`, đọc tài khoản Bob `403` và Sam gọi chức năng admin `403`. Không nói toàn bộ 26 ca đã đi qua OPA hoặc Burp.

## 5. Lời dẫn gợi ý

> “Đây là hai phiên bản của cùng API MiniBank với dữ liệu giả. Em dùng Burp bắt request Alice đọc tài khoản Bob: bản cũ trả 200, bản sửa trả 403. Sam gọi chức năng admin cũng bị chặn ở bản sửa dù token có scope phù hợp. Em gửi lặp cùng khóa: bản cũ trừ tiền hai lần, bản sửa giữ một giao dịch. Cuối cùng, em mở và chạy lại bộ 26 ca hồi quy. Bản sửa dùng OPA thật, có bằng chứng kiểm tra OPA riêng.”

## 6. Xử lý lỗi và kết thúc

| Hiện tượng | Cách xử lý |
|---|---|
| Không kết nối được Docker API | Mở Docker Desktop, đợi Engine chạy rồi chạy lại script. |
| Web không tải hoặc cổng bị chiếm | Chạy `docker compose ps`; xem log bằng `docker compose logs --tail 50 minibank_before minibank opa`. Giải phóng cổng 8000/8001 nếu bị dùng. |
| Burp Browser quay mãi | Kiểm tra **Proxy → Intercept**; bấm **Forward** hoặc chuyển **Intercept off**. |
| Burp không thấy request | Dùng đúng **Open Browser** của Burp và xem **HTTP history** kể cả khi Intercept off. |
| Token hết hạn | Bấm lại **Tạo phiên demo** trên trang đang dùng. |
| Số dư/mã giao dịch khác ví dụ | Chạy `docker compose down`, rồi chạy lại script để đặt lại dữ liệu. |

Kết thúc buổi demo:

```powershell
docker compose down
```
