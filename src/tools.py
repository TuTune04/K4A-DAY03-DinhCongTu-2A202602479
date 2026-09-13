"""
🛠️ TOOL DEFINITIONS & EXECUTION BACKEND
Mã nguồn chứa danh sách Tool Schemas (JSON Schema) và Execution Layer phục vụ cho MCP Server.
"""

import json
from datetime import date, timedelta
from typing import Dict, Any

# ==============================================================================
# 1. KHAI BÁO TOOL SCHEMAS CHUẨN NATIVE JSON SCHEMA (TASK 1.2)
# ==============================================================================

TOOLS_SCHEMA = [
    # Tool 1: Tra cứu thông tin tài liệu trong thư viện
    {
        "name": "library_query",
        "description": (
            "Tra cứu tài liệu trong thư viện theo mã tài liệu, ISBN, tiêu đề "
            "hoặc từ khóa; trả về vị trí và tình trạng mượn/trả."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "Mã tài liệu, ISBN, tiêu đề hoặc từ khóa cần tra cứu "
                        "(ví dụ: 'BK001' hoặc 'Artificial Intelligence')."
                    )
                },
                "reader_id": {
                    "type": "string",
                    "description": (
                        "Mã độc giả, dùng khi cần kiểm tra tình trạng mượn và "
                        "hạn trả của tài liệu (ví dụ: 'RD2026001')."
                    )
                }
            },
            "required": ["query"],
            "additionalProperties": False
        }
    },

    # Tool 2: Gia hạn tài liệu đang được độc giả mượn
    {
        "name": "renew_library_loan",
        "description": (
            "Gia hạn thời gian mượn một tài liệu cho độc giả sau khi hệ thống "
            "kiểm tra các điều kiện của thư viện."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "reader_id": {
                    "type": "string",
                    "description": "Mã độc giả yêu cầu gia hạn (ví dụ: 'RD2026001')."
                },
                "document_id": {
                    "type": "string",
                    "description": (
                        "Mã bản tài liệu đang được độc giả mượn "
                        "(ví dụ: 'BK001')."
                    )
                },
                "confirmation": {
                    "type": "boolean",
                    "description": (
                        "Xác nhận của người dùng rằng họ đồng ý thực hiện gia hạn."
                    )
                }
            },
            "required": ["reader_id", "document_id", "confirmation"],
            "additionalProperties": False
        }
    }
]

# ==============================================================================
# 2. MÔ PHỎNG DỮ LIỆU & HÀM THỰC THI TOOL (EXECUTION LAYER)
# ==============================================================================

MOCK_DOCUMENTS = {
    "BK001": {
        "title": "Artificial Intelligence: A Modern Approach",
        "isbn": "9780134610993",
        "authors": ["Stuart Russell", "Peter Norvig"],
        "location": "Tầng 3 - Kệ AI-02",
        "availability": "BORROWED",
        "reserved_by_another_reader": False
    },
    "BK002": {
        "title": "Deep Learning",
        "isbn": "9780262035613",
        "authors": ["Ian Goodfellow", "Yoshua Bengio", "Aaron Courville"],
        "location": "Tầng 3 - Kệ AI-04",
        "availability": "AVAILABLE",
        "reserved_by_another_reader": False
    },
    "BK003": {
        "title": "Designing Data-Intensive Applications",
        "isbn": "9781449373320",
        "authors": ["Martin Kleppmann"],
        "location": "Tầng 2 - Kệ CS-07",
        "availability": "BORROWED",
        "reserved_by_another_reader": True
    }
}

MOCK_READERS = {
    "RD2026001": {
        "full_name": "Nguyễn Văn An",
        "account_status": "ACTIVE",
        "unpaid_fine": 0,
        "loans": {
            "BK001": {
                "due_date": "2026-09-20",
                "renewal_count": 0,
                "max_renewals": 2
            },
            "BK003": {
                "due_date": "2026-09-18",
                "renewal_count": 0,
                "max_renewals": 2
            }
        }
    },
    "RD2026002": {
        "full_name": "Trần Thị Bình",
        "account_status": "BLOCKED",
        "unpaid_fine": 150000,
        "loans": {}
    }
}


def execute_library_query(query: str, reader_id: str = None) -> str:
    """Tra cứu tài liệu theo mã, ISBN, tiêu đề hoặc tên tác giả."""
    normalized_query = query.strip().casefold()
    if not normalized_query:
        return json.dumps({
            "status": "INVALID_ARGUMENT",
            "message": "Thông tin tra cứu không được để trống."
        }, ensure_ascii=False)

    normalized_reader_id = reader_id.strip().upper() if reader_id else None
    if normalized_reader_id and normalized_reader_id not in MOCK_READERS:
        return json.dumps({
            "status": "NOT_FOUND",
            "message": f"Không tìm thấy độc giả có mã '{normalized_reader_id}'."
        }, ensure_ascii=False)

    documents = []
    for document_id, document in MOCK_DOCUMENTS.items():
        searchable_values = [
            document_id,
            document["isbn"],
            document["title"],
            *document["authors"]
        ]
        if not any(normalized_query in value.casefold() for value in searchable_values):
            continue

        result = {"document_id": document_id, **document}
        if normalized_reader_id:
            loan = MOCK_READERS[normalized_reader_id]["loans"].get(document_id)
            result["reader_loan"] = loan
            result["borrowed_by_reader"] = loan is not None
        documents.append(result)

    if not documents:
        return json.dumps({
            "status": "NOT_FOUND",
            "query": query,
            "message": f"Không tìm thấy tài liệu phù hợp với '{query}'."
        }, ensure_ascii=False)

    return json.dumps({
        "status": "SUCCESS",
        "query": query,
        "reader_id": normalized_reader_id,
        "total": len(documents),
        "documents": documents
    }, ensure_ascii=False)


def execute_renew_library_loan(
    reader_id: str,
    document_id: str,
    confirmation: bool
) -> str:
    """Kiểm tra điều kiện và gia hạn một tài liệu thêm 14 ngày."""
    normalized_reader_id = reader_id.strip().upper()
    normalized_document_id = document_id.strip().upper()

    if confirmation is not True:
        return json.dumps({
            "status": "REJECTED",
            "reason_code": "CONFIRMATION_REQUIRED",
            "message": "Cần người dùng xác nhận trước khi thực hiện gia hạn."
        }, ensure_ascii=False)

    reader = MOCK_READERS.get(normalized_reader_id)
    if not reader:
        return json.dumps({
            "status": "NOT_FOUND",
            "reason_code": "READER_NOT_FOUND",
            "message": f"Không tìm thấy độc giả có mã '{normalized_reader_id}'."
        }, ensure_ascii=False)

    document = MOCK_DOCUMENTS.get(normalized_document_id)
    if not document:
        return json.dumps({
            "status": "NOT_FOUND",
            "reason_code": "DOCUMENT_NOT_FOUND",
            "message": f"Không tìm thấy tài liệu có mã '{normalized_document_id}'."
        }, ensure_ascii=False)

    loan = reader["loans"].get(normalized_document_id)
    if not loan:
        return json.dumps({
            "status": "REJECTED",
            "reason_code": "LOAN_NOT_FOUND",
            "message": "Độc giả hiện không mượn tài liệu này."
        }, ensure_ascii=False)

    if reader["account_status"] != "ACTIVE":
        return json.dumps({
            "status": "REJECTED",
            "reason_code": "ACCOUNT_BLOCKED",
            "message": "Tài khoản độc giả đang bị khóa."
        }, ensure_ascii=False)

    if reader["unpaid_fine"] > 0:
        return json.dumps({
            "status": "REJECTED",
            "reason_code": "UNPAID_FINE",
            "unpaid_fine": reader["unpaid_fine"],
            "message": "Độc giả cần thanh toán khoản phạt trước khi gia hạn."
        }, ensure_ascii=False)

    if document["reserved_by_another_reader"]:
        return json.dumps({
            "status": "REJECTED",
            "reason_code": "DOCUMENT_RESERVED",
            "message": "Không thể gia hạn vì tài liệu đã được độc giả khác đặt trước."
        }, ensure_ascii=False)

    if loan["renewal_count"] >= loan["max_renewals"]:
        return json.dumps({
            "status": "REJECTED",
            "reason_code": "RENEWAL_LIMIT_REACHED",
            "message": "Tài liệu đã đạt số lần gia hạn tối đa."
        }, ensure_ascii=False)

    old_due_date = date.fromisoformat(loan["due_date"])
    new_due_date = old_due_date + timedelta(days=14)
    loan["due_date"] = new_due_date.isoformat()
    loan["renewal_count"] += 1

    return json.dumps({
        "status": "SUCCESS",
        "renewal_id": f"RN-{normalized_document_id}-{loan['renewal_count']}",
        "reader_id": normalized_reader_id,
        "document_id": normalized_document_id,
        "old_due_date": old_due_date.isoformat(),
        "new_due_date": new_due_date.isoformat(),
        "renewal_count": loan["renewal_count"],
        "message": "Gia hạn tài liệu thành công."
    }, ensure_ascii=False)


# Router gọi tool thực tế
TOOL_ROUTER = {
    "library_query": execute_library_query,
    "renew_library_loan": execute_renew_library_loan
}

def dispatch_tool_call(tool_name: str, arguments: Dict[str, Any]) -> str:
    """Hàm trung chuyển thực thi tool"""
    if tool_name in TOOL_ROUTER:
        try:
            return TOOL_ROUTER[tool_name](**arguments)
        except Exception as e:
            return json.dumps({"status": "EXECUTION_ERROR", "error": str(e)}, ensure_ascii=False)
    return json.dumps({"status": "UNKNOWN_TOOL", "error": f"Tool '{tool_name}' không tồn tại!"}, ensure_ascii=False)
