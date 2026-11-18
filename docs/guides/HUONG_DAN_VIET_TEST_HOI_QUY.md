# Cách viết test hồi quy cho MiniBank API Lab

Tài liệu này hướng dẫn từ một quy tắc phân quyền đến một ca kiểm thử tự động trong dự án. Tệp cần đọc và sửa là `tests/demo.py`; quy tắc gốc nằm ở `app/policy/permission_matrix.csv`. Chỉ dùng tài khoản và dữ liệu giả của lab.

## 1. Hiểu test hồi quy đang kiểm tra điều gì

Test hồi quy là ca được giữ lại để chạy nhiều lần sau mỗi lần sửa mã. Nếu lỗi cũ tái xuất hiện hoặc chức năng hợp lệ bị chặn, ca đó phải báo thất bại. Với đề tài này, một ca cần xác định rõ:

`Ai gọi → hành động → tài nguyên → điều kiện quyền → kết quả mong đợi → trạng thái dữ liệu mong đợi`

Ví dụ: Alice (`customer`) gọi `GET /accounts/acc-b`, trong khi `acc-b` thuộc Bob. Quy tắc bảo mật yêu cầu từ chối. Bản trước sửa trả `200`; bản sau sửa phải trả `403`. Ca đối chứng là Alice đọc `acc-a` của mình và vẫn được `200`. Cặp ca **từ chối đúng + cho phép đúng** giúp phát hiện cả lỗ hổng lẫn việc sửa quá tay.

Không viết một test chỉ vì thấy API trả `403`: trước hết phải biết **vì sao** nó bị từ chối. Với BFLA, muốn chứng minh lỗi *vai trò*, hãy cấp scope `admin:users` cho Sam nhưng giữ role `support`. Nếu Sam thiếu scope, `403 missing_scope` chỉ chứng minh bước kiểm tra scope.

## 2. Bắt đầu từ ma trận quyền

Mở `app/policy/permission_matrix.csv`. Với mỗi dòng cần thử, ghi ra giấy hoặc bảng nháp:

| Trường | Ví dụ BOLA customer |
|---|---|
| Actor / role | `alice` / `customer` |
| Method / route | `GET /accounts/acc-b` |
| Scope cần có | `accounts:read` |
| Quan hệ với tài nguyên | `acc-b.owner = bob`, khác `sub = alice` |
| Kết quả theo policy | Từ chối, HTTP `403` |
| Ca đối chứng | `GET /accounts/acc-a` phải `200` |

Nếu một điều kiện chưa có trong ma trận, thêm dòng ma trận rồi mới thêm ca test. Một dòng ma trận có thể cần nhiều ca: quyền đúng, thiếu scope, sai vai trò, sai owner, thiếu token và tài nguyên không tồn tại là các nhánh khác nhau.

## 3. Chọn dữ liệu và viết kỳ vọng *trước khi viết code*

Ghi request cụ thể, ví dụ:

```http
GET /accounts/acc-b
Authorization: Bearer <token-lab-cua-alice>
```

Ghi kỳ vọng theo hai phiên bản:

| Kiểm tra | Trước sửa | Sau sửa |
|---|---:|---:|
| HTTP của Alice đọc `acc-b` | `200` để tái hiện lỗi | `403` để xác nhận đã chặn |
| HTTP của Alice đọc `acc-a` | `200` | `200` |

Với thao tác ghi như chuyển tiền, còn phải kiểm tra **trạng thái sau request**, không dừng ở HTTP. Ví dụ gửi cùng `Idempotency-Key` năm lần: bản sửa phải có đúng **một** giao dịch và số dư Alice từ `100` còn `90`. Chỉ kiểm tra cả năm response đều `200` sẽ bỏ sót việc trừ tiền năm lần.

## 4. Xem khung test hiện tại

Trong `tests/demo.py`:

1. `REQUESTS` mô tả request để in vào báo cáo.
2. `auth(...)` tạo token lab với `sub`, `role` và `scope` đã chọn.
3. `one(mode, case)` tạo ứng dụng mới, gửi request và tính biến `safe`.
4. `CASES` quyết định các ca được chạy.
5. `GROUPS` xếp ca vào nhóm thống kê; chương trình kiểm tra mỗi ca trong `CASES` phải xuất hiện đúng một lần trong `GROUPS`.
6. `main()` chạy tất cả ca trên `before` và `fixed`, ghi JSON, HTML, JUnit và báo cáo.

`one()` dùng `httpx.ASGITransport`, nghĩa là 26 ca gọi ứng dụng Python **trực tiếp trong container kiểm thử**, không gửi qua Burp và không bật OPA sidecar. Mỗi lần gọi `one()` tạo một app và dữ liệu mới, nên ca trước không làm thay đổi số dư của ca sau. Kiểm tra OPA đang chạy là bước riêng trong `tests/verify_opa.py`.

## 5. Đọc một ca BOLA đã có, từng dòng

Đây là đoạn tương ứng trong `one()`:

```python
elif case == "BOLA customer":
    r = await c.get("/accounts/acc-b", headers=auth("alice"))
    safe = r.status_code == 403
```

- `auth("alice")` tạo token có `sub=alice` và scope mặc định chứa `accounts:read`.
- `c.get(...)` gửi request tới `acc-b`; dữ liệu lab khai báo owner là Bob.
- `safe` là điều kiện bảo mật muốn giữ sau khi sửa. Ở bản cũ `safe=False` vì HTTP `200`; ở bản mới `safe=True` vì HTTP `403`.

Ca đối chứng ngay bên cạnh là:

```python
elif case == "Customer hợp lệ":
    r = await c.get("/accounts/acc-a", headers=auth("alice"))
    safe = r.status_code == 200
```

Với API thay đổi dữ liệu, tăng độ chặt của `safe` bằng cách kiểm tra `lab.accounts`, `lab.profiles` hoặc `lab.transfers`. Ca `"Chuyển từ tài khoản khác"` trong tệp hiện tại kiểm cả HTTP `403` lẫn số dư Bob vẫn là `100`.

## 6. Tự thêm một ca mới vào bộ hiện có

Ví dụ muốn tách riêng lỗi BFLA ở `GET /admin/users`: Sam có scope `admin:users` nhưng role vẫn là `support`. Bản cũ cho phép, bản sửa khi chạy ASGI không bật OPA trả `403 forbidden`.

**Bước 6.1 — Ma trận.** Thêm một dòng trong `app/policy/permission_matrix.csv` cho `support / GET /admin/users / scope hợp lệ nhưng role không phải admin / deny`. Đặt `policy_id` duy nhất và `evidence_case` đúng tên ca. Nếu quản lý ID policy trong mã, đối chiếu để ID trong log không mâu thuẫn với ma trận.

**Bước 6.2 — Mô tả.** Thêm vào `REQUESTS` trong `tests/demo.py`:

```python
"BFLA danh sách sai vai trò": "GET /admin/users; actor=sam; role=support; scope=admin:users",
```

**Bước 6.3 — Request và điều kiện đạt.** Thêm nhánh vào `one()` trước nhánh `else: raise ValueError(case)`:

```python
elif case == "BFLA danh sách sai vai trò":
    r = await c.get(
        "/admin/users",
        headers=auth("sam", "support", "admin:users"),
    )
    safe = r.status_code == 403 and r.json().get("detail") == "forbidden"
```

Ở đây `admin:users` đã có trong token, nên ca này kiểm tra **vai trò**, không lẫn với ca `"Thiếu scope admin"`. Trong bộ ASGI, bản sau trả `forbidden`; khi chạy qua Docker Compose có OPA, cùng request có thể trả `opa_denied`. Đừng áp kỳ vọng `detail` của môi trường này sang môi trường kia.

**Bước 6.4 — Đăng ký ca.** Thêm đúng tên `"BFLA danh sách sai vai trò"` vào `CASES`, rồi thêm **một lần** vào nhóm `"Chặn đúng ca tấn công"` trong `GROUPS`. Nếu quên một trong hai chỗ, ca không chạy hoặc lệnh `assert` dừng chương trình.

**Bước 6.5 — Chạy và xem lỗi.** Khi lab Compose đang bật:

```powershell
cd D:\attt\de_tai_27
docker compose --profile tests run --rm --build regression
```

Cần `--build` sau khi sửa `tests/demo.py` vì tệp test được **COPY vào image** ở `Dockerfile.tests`; `run` không tự cập nhật mã đã đóng gói. Sau lần build đó, chạy lại mà không sửa mã có thể dùng `docker compose --profile tests run --rm --no-deps regression`.

Khi thêm một ca, số tổng dự kiến thành **27**, không còn 26. Nếu đã sửa mã test mà output vẫn là 26, khả năng cao bạn chưa build lại image hoặc chưa thêm tên vào `CASES`.

## 7. Đọc kết quả để biết test thực sự đạt

Sau khi chạy, xem:

```powershell
Invoke-Item .\tests\results\demo.html
Get-Content .\tests\results\REPORT.md
Get-Content .\tests\results\opa_runtime.json
```

| Tệp | Dùng để làm gì |
|---|---|
| `demo.html` | Trình chiếu bảng HTTP trước/sau và số ca bản sửa đạt. |
| `before_after.json` | Xem request mô tả, HTTP, response, `safe`, số dư, số giao dịch, log và request ID từng ca. |
| `junit.xml` | Đưa kết quả cho công cụ CI đọc. |
| `REPORT.md` | Xem tổng hợp theo nhóm và số đo độ trễ mẫu. |
| `opa_runtime.json` | Xem kiểm tra OPA và API thật trong Compose; khác bộ 26 ca ASGI. |

Đừng coi HTTP `200` là “test đạt” trong mọi trường hợp. Với ca hợp lệ, `200` là đúng. Với BOLA hoặc BFLA, `200` ở bản cũ là **bằng chứng lỗi**, còn `403` ở bản sửa mới đúng. Với idempotency, cả hai lần gửi có thể đều `200`, nên phải so mã giao dịch và số dư.

## 8. Kiểm tra một test có giá trị hay chưa

Trước khi giữ ca vào bộ hồi quy, tự kiểm tra năm câu:

1. Nó bám một dòng ma trận hoặc một quy tắc nghiệp vụ rõ ràng chưa?
2. Token có đúng `sub`, `role`, `scope` để chỉ kiểm **một** nguyên nhân từ chối chưa?
3. Nó có một ca cho phép đối chứng để phát hiện chặn nhầm chưa?
4. Nếu API ghi dữ liệu, nó đã kiểm số dư, vai trò hoặc số giao dịch **sau request** chưa?
5. Nó chạy lại được với dữ liệu khởi tạo cố định, không phụ thuộc ca khác hay token thật chứ?

Quy trình ngắn gọn là: **ma trận → dữ liệu và kỳ vọng → request → assertion HTTP + trạng thái → ca đối chứng → chạy trước/sau → lưu kết quả → chạy lại sau mỗi lần sửa**.
