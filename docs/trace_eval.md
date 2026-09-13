# 📊 BÁO CÁO THU HOẠCH NGHIỆM THU BÀI LAB 3 (BƯỚC 3 — SUBMISSION ARTIFACT)

> **Họ và Tên Học viên:** Đinh Công Tú 
> **Mã Sinh Viên / Mã Học viên:** 2A202602479
> **Chủ đề Lựa chọn:** Gợi ý 1.2 — Trợ lý Quản lý Thư viện & Tài liệu

---

## 1. BẢNG CHẤM ĐIỂM AGENTIC FIT SCORING MATRIX (ĐÁNH GIÁ CHỦ ĐỀ)

| Tiêu chí Đánh giá | Mức độ (1 - 5) | Giải trình chi tiết lý do chọn điểm |
| :--- | :---: | :--- |
| **1. Multi-step Reasoning** | 4 / 5 | Agent cần hiểu nhu cầu của người dùng, xác định tài liệu, tra cứu vị trí và tình trạng, kiểm tra điều kiện mượn hoặc gia hạn, rồi tổng hợp câu trả lời hay thực hiện yêu cầu. Quy trình có nhiều bước nối tiếp nhưng độ phức tạp suy luận chưa quá cao. |
| **2. Tool Interaction** | 5 / 5 | Hệ thống phải kết nối MCP Server và cơ sở dữ liệu thư viện để tra cứu danh mục, vị trí, bản sao khả dụng, hồ sơ mượn/trả; đồng thời gọi công cụ hành động để gia hạn tài liệu. |
| **3. Dynamic Decision** | 5 / 5 | Hành động tiếp theo phụ thuộc trực tiếp vào kết quả tra cứu: sách còn hay đã được mượn, tài khoản có hợp lệ không, tài liệu có người đặt trước không, đã đạt giới hạn gia hạn chưa và có khoản phạt quá hạn không. |
| **4. Long Horizon Goal** | 3 / 5 | Agent cần duy trì mục tiêu và ngữ cảnh qua vài lượt để làm rõ tên sách, chọn đúng bản tài liệu, xác nhận tài khoản và hoàn tất gia hạn. Tuy nhiên, đa số tác vụ có thể kết thúc trong một phiên ngắn. |
| **TỔNG ĐIỂM AGENTIC FIT** | **17 / 20** | **17/20 > 12/20: Bài toán rất phù hợp triển khai Agentic System.** |

---

## 2. TRÍCH XUẤT KẾT QUẢ WATERFALL TRACE LOG (SAU KHI CHẠY TEST SUITE TRÊN API THẬT)

> ⚠️ **YÊU CẦU NGHIỆM THU:** Mở tệp `.env` điền `GEMINI_API_KEY` (hoặc `OPENAI_API_KEY`) để kết nối LLM thật trước khi thực thi `python src/app.py --all`. Bài nộp chỉ dùng Mock Offline Provider sẽ không đạt điểm nghiệm thực tế.

**Trạng thái hiện tại:** File vết có 10 sự kiện; tất cả đều có `step`, `query`, `action_type` và `latency_ms`. Các sự kiện gọi công cụ có đủ `tool_name`, `arguments` và `observation`. Đoạn dưới đây được sinh bằng `MockOfflineProvider` để kiểm tra luồng; cần chạy lại bằng API thật trước khi nghiệm thu chính thức.

Đoạn trace tiêu biểu cho luồng đa bước tra cứu rồi gia hạn tài liệu:

```json
[
  {
    "step": 1,
    "query": "Tôi là độc giả RD2026001. Hãy kiểm tra tài liệu BK003 và gia hạn giúp tôi nếu đủ điều kiện; tôi xác nhận đồng ý gia hạn.",
    "action_type": "TOOL_EXECUTION",
    "tool_name": "library_query",
    "arguments": {
      "query": "BK003",
      "reader_id": "RD2026001"
    },
    "observation": {
      "status": "SUCCESS",
      "query": "BK003",
      "reader_id": "RD2026001",
      "total": 1,
      "documents": [
        {
          "document_id": "BK003",
          "title": "Designing Data-Intensive Applications",
          "isbn": "9781449373320",
          "authors": [
            "Martin Kleppmann"
          ],
          "location": "Tầng 2 - Kệ CS-07",
          "availability": "BORROWED",
          "reserved_by_another_reader": true,
          "reader_loan": {
            "due_date": "2026-09-18",
            "renewal_count": 0,
            "max_renewals": 2
          },
          "borrowed_by_reader": true
        }
      ]
    },
    "latency_ms": 1582.78
  },
  {
    "step": 2,
    "query": "Tôi là độc giả RD2026001. Hãy kiểm tra tài liệu BK003 và gia hạn giúp tôi nếu đủ điều kiện; tôi xác nhận đồng ý gia hạn.",
    "action_type": "FINAL_ANSWER",
    "thought": "OpenAI phản hồi trực tiếp bằng văn bản (không cần gọi công cụ).",
    "output": "Tài liệu BK003 (\"Designing Data-Intensive Applications\") hiện đang được mượn và đã được đặt trước bởi một độc giả khác. Hơn nữa, tài liệu này đã có 0 lần gia hạn và cho phép tối đa 2 lần gia hạn. Tuy nhiên, do tài liệu đã được đặt trước, bạn không thể gia hạn lần mượn này.\n\nVậy bạn không thể gia hạn tài liệu BK003. Nếu bạn cần hỗ trợ với tài liệu khác hoặc có câu hỏi nào khác, hãy cho tôi biết!",
    "latency_ms": 1558.02
  }
]
```

---

## 3. TỔNG KẾT KẾT QUẢ NGHIỆM THU & NỘP BÀI

- [ ] Đã điền API Key thật trong `.env` và xác nhận Agent chạy mượt mà trên LLM API thật (Gemini/OpenAI).
- **Tổng số Test Cases đã chạy thành công:** 5 / 5 test cases.
- **Số lượt gọi Tool qua MCP Server chính xác:** 5 lượt.
- **Kết quả đẩy Repo nộp bài:** [ ] Đã Commit và Push mã nguồn thành công lên GitHub cá nhân.

---

> ✅ **HOÀN TẤT NỘP BÀI:** Sao chép đường link GitHub Repository cá nhân của bạn và dán vào ô nộp bài trên hệ thống LMS VLearn để hoàn tất Bài Lab 3!
