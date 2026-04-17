# Day 12 Lab - Mission Answers

## Part 1: Localhost vs Production

### Exercise 1.1: Anti-patterns found
1. **API key & Credentials hardcoded:** Để trực tiếp `OPENAI_API_KEY` và `DATABASE_URL` trong mã nguồn. Nếu đẩy code lên GitHub sẽ bị lộ secret ngay lập tức.
2. **Không có config management:** Hardcode các cấu hình vào trong code (ví dụ: `DEBUG = True`, MAX_TOKENS). Không đọc qua environment variables làm mất đi độ linh hoạt.
3. **Sử dụng `print()` thay vì logging bài bản:** In log có thể làm lộ secret key ra màn hình, đồng thời không có tính cấu trúc khiến việc monitor ở production là bất khả thi.
4. **Không có health check endpoint:** Khi app bị lỗi hay crash ngầm, hệ thống cloud/platform không thể nhận biết để tự động restart lại máy chủ.
5. **Host và Port cố định, bật chế độ debug (reload=True):** Cấu hình `host="localhost"` không cho IP ngoài truy cập và port=8000 cố định kìm hãm khi deploy trên Cloud (vì Cloud sẽ cấp Port động). Bật reload=True gây tốn tài nguyên hệ thống ở môi trường Production.

### Exercise 1.3: Comparison table
| Feature | Develop | Production | Why Important? |
|---------|---------|------------|----------------|
| Config  | Hardcode (gán chết trong code) | Dùng Environment Variables | Giữ config linh hoạt giữa các môi trường, đảm bảo bảo mật thông tin nhạy cảm. |
| Health check  | Không có | Cấu hình `/health` (Liveness) và `/ready` (Readiness) | Hỗ trợ cho Cloud Platform (Kubernetes/Railway) monitor và tự động route request hoặc restart tiến trình. |
| Logging  | Lệnh `print()`, dễ lộ secret | Structured JSON logging | Quản lý log đồng nhất để các hệ thống Log Aggregator thu thập dễ dàng, và giấu nội dung nhạy cảm. |
| Shutdown  | Tắt tiến trình đột ngột ngay lập tức | Graceful shutdown (qua Signal) | Chờ cho những current requests đang xử lý dở được hoàn tất nốt, tránh loss data. |
| Host / Port | `localhost` và port cứng `8000` | `0.0.0.0` và cổng động từ `$PORT` | Giúp ứng dụng nhận liên kết external từ ngoài container, đáp ứng dynamic binding port của cloud host. |

## Part 2: Docker

### Exercise 2.1: Dockerfile questions
1. Base image: `python:3.11` (với develop) và `python:3.11-slim` (với production AS builder/runtime).
2. Working directory: `/app`
3. Tại sao COPY requirements.txt trước?: Mục đích là vận dụng tính năng **Layer Cache** của Docker. Do package ít khi thay đổi hơn code app, nếu chép trước và chạy `pip install`, Docker sẽ cache nguyên mảng cài đặt này ở các lần build tiết theo (giúp tiết kiệm rất nhiều thời gian trừ phi `requirements.txt` vừa cập nhật).
4. CMD vs ENTRYPOINT khác nhau thế nào?: `CMD` cung cấp một lệnh shell mặc định để chạy container, tuy nhiên rất dễ bị ghi đè trực tiếp thông qua đuôi tham số của dòng `docker run image <lệnh ghi đè>`. Trong khi `ENTRYPOINT` quy định app được chạy cố định, khó ghi đè hơn và lấy phần thừa của `docker run` đem vào làm argument truyền thêm cho file chạy app.

### Exercise 2.3: Image size comparison
- Develop: 1.66 GB
- Production: 236 MB
- Difference: Dung lượng cực kỳ tối ưu, giảm khoảng ~86% từ 1.66GB xuống còn 236MB

## Part 3: Cloud Deployment

### Exercise 3.1: Railway deployment
- URL: https://day12-production-ad58.up.railway.app
- Screenshot: [https://github.com/phucx314/2A202600424-TaVinhPhuc-Day12/blob/main/extras/screenshots/image.png](./extras/screenshots/image.png)

### Exercise 3.2: Deploy Render / Config files comparison
Dựa trên rubric chấm điểm, tôi chọn phương án So sánh config thay vì cài đặt song song nền tảng Render để đỡ tốn thời gian. Bên dưới là sự khác biệt giữa `render.yaml` và `railway.toml`:
1. **Quản lý quy mô (Scope):**
   - `render.yaml`: Có thể triển khai được nhiều Services và Addons phụ trợ cùng một lúc (Chỉ bằng một file có thể bật lên vừa Web API (`type: web`) lại vừa Database (`type: redis`)).
   - `railway.toml`: Thường chỉ cấu hình scope cho một repo/service cụ thể theo kiểu `[build]` và `[deploy]`.
2. **Quản lý Biến môi trường (EnvVars):** 
   - `render.yaml`: Cho phép khai báo biến nội tuyến bằng JSON, bật cờ như `generateValue: true` để bắt server tự sinh random token, hoặc chặn sync biến nhạy cảm.
   - `railway.toml`: Tránh việc commit biến nội tuyến, toàn bộ biến được quản lý rời trên Railway UI hoặc qua CLI `.env`.
3. **Cấu hình Build Environment:** 
   - `render.yaml`: Yêu cầu phải tự define OS môi trường (`runtime: python`) cài lệnh buildCommand, startCommand thủ công rạch ròi.
   - `railway.toml`: Sử dụng một hệ thống gọi là `builder = "NIXPACKS"` tự động do thám code và chọn công cụ biên dịch siêu dễ (Auto-magic).

## Part 4: API Security

### Exercise 4.1 & 4.3: Q&A Lý thuyết bảo mật
**Về API Key (Exercise 4.1):**
- **Được check ở đâu?** Trong code, nó kiểm tra ở `app.py` thông qua Dependency injection `verify_api_key` chặn ngay cổng của API Endpoint `/ask`.
- **Sai key?** Server xua đuổi không thương tiếc bằng lệnh raise `401 Unauthorized` hoặc `403 Forbidden`.
- **Rotate key thế nào?** Gen một string mã số bí mật mới, cấp cho Client, thay giá trị vào biến môi trường Server (`AGENT_API_KEY`) rồi reload/restart là xong.

**Về Rate Limiting (Exercise 4.3):**
- **Dùng thuật toán gì?** Dùng **Sliding Window Counter** (mượt hơn Token Bucket vì nó trượt thời gian chính xác từng giây qua `deque` array).
- **Limit request?** Giới hạn mặc định cho người dùng trần gian là **10 requests/minute**.
- **Làm sao bypass cấp Admin?** Trong code dùng chiêu tạo sẵn 2 nhân viên gác cổng: `rate_limiter_user` (10 requests) và `rate_limiter_admin` (100 requests). Nếu Role là Admin nó sẽ ré nhánh cho gặp nhân viên nới rào lên 100 lần.

### Exercise 4.1-4.3: Test results
**1. Lỗi thiếu API Key (401 Unauthorized)**
```bash
curl -X POST http://localhost:8000/ask -H "Content-Type: application/json" -d '{"question": "Hello"}'
# Kết quả trả về chặn kết nối: 
# HTTP/1.1 401 Unauthorized
# phucx314@ip6-dynamic-adsl:~$ curl -X POST http://localhost:8000/ask -H "Content-Type: application/json" -d '{"question": "Hello"}'
{"detail":"Authentication required. Include: Authorization: Bearer <token>"}
```

**2. Test JWT Authentication Flow thành công (200 OK)**
```bash
# Xin cấp JWT token bằng account
curl -X POST http://localhost:8000/auth/token -H "Content-Type: application/json" -d '{"username": "student", "password": "demo123"}'
# HTTP/1.1 200 OK
#phucx314@ip6-dynamic-adsl:~$ curl -X POST http://localhost:8000/auth/token -H "Content-Type: application/json" -d '{"username": "student", "password": "demo123"}'
{"access_token":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzdHVkZW50Iiwicm9sZSI6InVzZXIiLCJpYXQiOjE3NzY0MTg2MzcsImV4cCI6MTc3NjQyMjIzN30.0FyETzpfgbMdFQp7-Y0w4FxcUhDHTtwdDVZr1MowoAQ","token_type":"bearer","expires_in_minutes":60,"hint":"Include in header: Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."}

# Bắn request vào API bằng token xịn
curl -X POST http://localhost:8000/ask -H "Authorization: Bearer eyJhbGciOi..." -H "Content-Type: application/json" -d '{"question": "What is JWT?"}'
# HTTP/1.1 200 OK
# phucx314@ip6-dynamic-adsl:~$ curl -X POST http://localhost:8000/ask -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzdHVkZW50Iiwicm9sZSI6InVzZXIiLCJpYXQiOjE3NzY0MTg2MzcsImV4cCI6MTc3NjQyMjIzN30.0FyETzpfgbMdFQp7-Y0w4FxcUhDHTtwdDVZr1MowoAQ" -H "Content-Type: application/json" -d '{"question": "What is JWT?"}'
{"question":"What is JWT?","answer":"Đây là câu trả lời từ AI agent (mock). Trong production, đây sẽ là response từ OpenAI/Anthropic.","usage":{"requests_remaining":9,"budget_remaining_usd":2.1e-05}}
```

**3. Lỗi Rate Limiting (429 Too Many Requests)**
```bash
# Sau khi bắn liên hồi quá số lượng (VD: >= 10 request / phút)
curl -X POST http://localhost:8000/ask -H "Authorization: Bearer eyJhbGci..." -H "Content-Type: application/json" -d '{"question": "Spam 11 lần"}'
# HTTP/1.1 429 Too Many Requests
# phucx314@ip6-dynamic-adsl:~$ curl -X POST http://localhost:8000/ask -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzdHVkZW50Iiwicm9sZSI6InVzZXIiLCJpYXQiOjE3NzY0MTg2MzcsImV4cCI6MTc3NjQyMjIzN30.0FyETzpfgbMdFQp7-Y0w4FxcUhDHTtwdDVZr1MowoAQ" -H "Content-Type: application/json" -d '{"question": "Spam 11 lần"}'
{"detail":{"error":"Rate limit exceeded","limit":10,"window_seconds":60,"retry_after_seconds":50}}
```

### Exercise 4.4: Cost guard implementation
Do hệ thống deploy lên Cloud hoặc gánh nhiều request chia thành nhiều Container, nên Memory lưu bằng Dictionary thông thường sẽ bị "reset" liên tục và không đồng bộ, làm ngân sách bị ảo. Do đó, cách tiếp cận chuẩn xác ở đây là sử dụng **Redis** để lưu `budget`:
- Biến mỗi người dùng với ID thành một khóa theo tháng (Ví dụ: `budget:user_id:2026-04`).
- Sử dụng hàm atomic `incrbyfloat(key, cost)` để cập nhật tổng tiền tiêu một cách chính xác mà không sợ conflict.
- Thêm điều kiện kiểm tra nếu `current_balance + cost > 10.0` thì trả về trạng thái từ chối dịch vụ.
- Thiết lập tính năng tự xoá file `expire(key, 32 days)` cho khoá sau một tháng để giải phóng Redis.

## Part 5: Scaling & Reliability

### Exercise 5.1-5.5: Implementation notes

**1. Health & Readiness checks (Ex 5.1):** 
Thiết kế tách bạch hai endpoint riêng: `/health` để đơn giản là trả về 200 OK để Docker/Platform biết app chưa sập và `/ready` để kiểm tra chuyên sâu để ping thẳng vào DB/Redis xem có ổn không, nếu đứt cáp hoặc Database sập sẽ trả về 503 để Load Balancer Nginx lập tức ngừng bơm traffic vào Node đó.

**2. Graceful Shutdown (Ex 5.2):** 
Viết thêm hook bắt tín hiệu của OS (như `SIGTERM` hay `SIGINT` từ lệnh docker stop). Khi nhận lệnh tắt, Agent sẽ thông báo ngắt kết nối không nhận thêm request mới, nhưng vẫn kiên nhẫn đợi các current requests chạy xong nốt, và đóng mọi connection pool tới Redis một cách an toàn để chống mất mát dữ liệu (Data Corruption).

**3. Stateless Design (Ex 5.3):**
Chuyển hoá bộ nhớ AI chat (Conversation History) từ biến bộ nhớ RAM của file chạy Python ngầm định sang cơ sở dữ liệu in-memory tập trung là **Redis**. Vì nếu để ở code thì mỗi Container lại mang một ký ức riêng (bị split-brain). Dời qua Redis giúp các agent code trở thành các chiến binh "vô sản" (Stateless), khi đó App Scale mở rộng đến bao nhiêu Container thì dữ liệu chat vẫn đồng bộ và không bị bay hơi khi restart.

**4. Nginx Load Balancing (Ex 5.4 & 5.5):**
Khởi tạo cấu trúc nhiều Containers song song (`docker compose --scale agent=3`) kèm 1 Container Nginx Proxy chắn đằng trước. Nginx sẽ đóng vai là "Cán bộ phân buồng" sử dụng thuật toán round-robin hoặc least_conn, chia đều luồng request đến các Agent rảnh rỗi. Nginx có cài đặt Healthcheck liên tục dòm ngó cái `/ready` phía trên để nếu rủi 1 Agent lăn ra ngủ héo, nó tự đá khách (traffic) sang 2 Agent khoẻ mạnh còn lại, giúp hệ thống không bao giờ bị dán đoạn downtime!