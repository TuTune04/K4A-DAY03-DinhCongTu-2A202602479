"""
🚀 CORE AGENT APPLICATION (DAY 03: CHATBOT VS REACT AGENT)
Thực thi so sánh giữa Chatbot Baseline (Cấp 2) và ReAct Agent kết nối MCP Server (Cấp 3).
"""

import json
import os
import sys
import time
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from mcp_server import MCPAcademicServer
from prompts import (
    CHATBOT_BASELINE_PROMPT,
    REACT_AGENT_SYSTEM_PROMPT,
    MAX_ITERATIONS
)
from providers import get_llm_provider

load_dotenv()

def load_test_cases():
    """Tải danh sách 5 test cases từ config/test_cases.json hoặc config/test_cases.example.json"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")
    if not os.path.exists(config_path):
        example_path = os.path.join(base_dir, "config", "test_cases.example.json")
        if os.path.exists(example_path):
            print("⚠️ [CONFIG NOTICE]: Chưa thấy file 'config/test_cases.json'. Đang dùng mẫu 'config/test_cases.example.json'.")
            print("👉 Hãy chạy: copy config/test_cases.example.json config/test_cases.json và viết test cases theo đề tài của bạn!\n")
            config_path = example_path
        else:
            config_path = "test_cases.json"
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_waterfall_trace(trace_data: list):
    """Ghi vết log Waterfall Trace Log ra file docs/trace_waterfall.json"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    docs_dir = os.path.join(base_dir, "docs")
    os.makedirs(docs_dir, exist_ok=True)
    trace_path = os.path.join(docs_dir, "trace_waterfall.json")
    with open(trace_path, "w", encoding="utf-8") as f:
        json.dump(trace_data, f, ensure_ascii=False, indent=2)
    print(f"📊 [OBSERVABILITY]: Đã lưu {len(trace_data)} sự kiện Waterfall Trace tại '{trace_path}'!")


def run_baseline_chatbot(user_query: str, provider):
    """Chạy Chatbot gốc (Cấp 2) không có công cụ gọi Tool"""
    print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")
    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    print(f"🤖 Chatbot phản hồi:\n{response}")


def build_final_answer(tool_name: str, observation: dict) -> str:
    """Tạo câu trả lời ngắn gọn, chỉ dựa trên dữ liệu Tool trả về."""
    status = observation.get("status")
    if status != "SUCCESS":
        return observation.get(
            "message",
            f"Công cụ trả về trạng thái {status or 'không xác định'}."
        )

    if tool_name == "library_query":
        documents = observation.get("documents", [])
        if not documents:
            return "Không tìm thấy tài liệu phù hợp."

        lines = []
        for document in documents:
            availability = {
                "AVAILABLE": "có thể mượn",
                "BORROWED": "đang được mượn"
            }.get(document.get("availability"), document.get("availability", "không rõ"))
            line = (
                f"{document.get('document_id', '')} – {document.get('title', '')}; "
                f"vị trí: {document.get('location', 'không rõ')}; "
                f"tình trạng: {availability}"
            )
            reader_loan = document.get("reader_loan")
            if reader_loan:
                line += f"; hạn trả: {reader_loan.get('due_date', 'không rõ')}"
            lines.append(line + ".")
        return "Kết quả tra cứu:\n- " + "\n- ".join(lines)

    if tool_name == "renew_library_loan":
        return (
            f"Gia hạn thành công tài liệu {observation.get('document_id', '')}. "
            f"Hạn trả mới là {observation.get('new_due_date', 'không rõ')} "
            f"(hạn cũ: {observation.get('old_due_date', 'không rõ')})."
        )

    return observation.get(
        "message",
        f"Đã hoàn tất xử lý: {json.dumps(observation, ensure_ascii=False)}"
    )


def run_react_agent(user_query: str, provider, mcp_server: MCPAcademicServer) -> list:
    """
    [REACT AGENT LOOP] Thực thi vòng lặp Thought -> Action -> Observation với MCP Server
    Trả về danh sách trace log của phiên thực thi.
    """
    print(f"\n🤖 [REACT AGENT] Câu hỏi: {user_query}")
    
    trace_logs = []
    tools_list = mcp_server.list_tools()
    agent_input = user_query
    executed_calls = set()
    last_tool_name = None
    last_observation = None

    for step in range(1, MAX_ITERATIONS + 1):
        step_start_time = time.perf_counter()
        print(f"\n--- 🔄 Vòng lặp ReAct Loop (Step {step}/{MAX_ITERATIONS}) ---")

        # Gọi LLM với Native Tool Calling Specs
        llm_response = provider.generate_with_tools(
            agent_input,
            tools_list,
            system_prompt=REACT_AGENT_SYSTEM_PROMPT
        )
        latency_ms = round((time.perf_counter() - step_start_time) * 1000, 2)

        thought = llm_response.get("thought", "Đang suy luận...")
        print(f"🧠 [Thought]: {thought}")

        # Trường hợp 1: LLM quyết định trả lời bằng văn bản trực tiếp
        if llm_response.get("type") == "text":
            final_content = llm_response.get("content", "")
            print(f"🏁 [Final Answer]: {final_content}")
            trace_logs.append({
                "step": step,
                "query": user_query,
                "action_type": "FINAL_ANSWER",
                "thought": thought,
                "output": final_content,
                "latency_ms": latency_ms
            })
            break

        # Trường hợp 2: LLM đề xuất gọi Tool (Action)
        if llm_response.get("type") == "tool_call":
            tool_name = llm_response.get("tool_name")
            arguments = llm_response.get("arguments", {})

            print(f"🛠️ [Action Proposed]: {tool_name}({arguments})")

            call_key = (tool_name, json.dumps(arguments, ensure_ascii=False, sort_keys=True))
            if call_key in executed_calls:
                final_answer = "Agent đã dừng vì phát hiện một Tool Call bị lặp lại."
                print(f"🏁 [Final Answer]: {final_answer}")
                trace_logs.append({
                    "step": step,
                    "query": user_query,
                    "action_type": "FINAL_ANSWER",
                    "thought": "Ngăn vòng lặp Tool Call trùng lặp.",
                    "output": final_answer,
                    "latency_ms": latency_ms
                })
                break
            executed_calls.add(call_key)

            # Thực thi Tool qua MCP Server
            mcp_result = mcp_server.call_tool(tool_name, arguments)
            obs_data = mcp_result.get("result", {})
            obs_str = json.dumps(obs_data, ensure_ascii=False)
            print(f"👁️ [Observation từ MCP Server]: {obs_str}")

            trace_logs.append({
                "step": step,
                "query": user_query,
                "action_type": "TOOL_EXECUTION",
                "tool_name": tool_name,
                "arguments": arguments,
                "observation": obs_data,
                "latency_ms": latency_ms
            })

            last_tool_name = tool_name
            last_observation = obs_data

            # Tra cứu là bước trung gian nếu người dùng còn yêu cầu gia hạn.
            needs_next_step = (
                tool_name == "library_query"
                and "gia hạn" in user_query.casefold()
                and obs_data.get("status") == "SUCCESS"
            )
            if needs_next_step:
                agent_input = (
                    f"Yêu cầu ban đầu: {user_query}\n"
                    f"Observation từ library_query: {obs_str}\n"
                    "Hãy quyết định bước tiếp theo. Chỉ gọi renew_library_loan nếu "
                    "đã xác định đúng độc giả, tài liệu và người dùng đã xác nhận."
                )
                continue

            final_answer = build_final_answer(tool_name, obs_data)
            print("🧠 [Thought]: Đã nhận Observation và tổng hợp câu trả lời.")
            print(f"🏁 [Final Answer]: {final_answer}")
            trace_logs.append({
                "step": step + 1,
                "query": user_query,
                "action_type": "FINAL_ANSWER",
                "thought": "Tổng hợp kết quả từ MCP Server thành công.",
                "output": final_answer,
                "latency_ms": 10.0
            })
            break

        final_answer = "LLM trả về kiểu phản hồi không hợp lệ."
        print(f"🏁 [Final Answer]: {final_answer}")
        trace_logs.append({
            "step": step,
            "query": user_query,
            "action_type": "FINAL_ANSWER",
            "thought": "Không nhận diện được kiểu phản hồi từ LLM.",
            "output": final_answer,
            "latency_ms": latency_ms
        })
        break
    else:
        final_answer = build_final_answer(last_tool_name, last_observation or {})
        print(f"🏁 [Final Answer]: {final_answer}")
        trace_logs.append({
            "step": MAX_ITERATIONS + 1,
            "query": user_query,
            "action_type": "FINAL_ANSWER",
            "thought": "Đã đạt giới hạn số vòng lặp.",
            "output": final_answer,
            "latency_ms": 0.0
        })

    return trace_logs


if __name__ == "__main__":
    print("==========================================================")
    print("📚 VINUNI LIBRARY ASSISTANT - DAY 03 LAB")
    print("==========================================================")
    
    provider = get_llm_provider()
    mcp_server = MCPAcademicServer()
    
    print(f"🔌 LLM Provider: {provider.__class__.__name__}")
    print(f"🌐 MCP Server: {mcp_server.server_name}\n")
    
    tests = load_test_cases()
    print(f"✅ Đã tải thành công {len(tests)} Test Cases thử nghiệm.\n")
    
    if "--interactive" in sys.argv:
        print("🎮 [INTERACTIVE MODE] Trò chuyện trực tiếp với ReAct Agent:")
        print("💡 Gợi ý câu hỏi thử nghiệm:")
        print("   - Khả năng hỗ trợ: 'Bạn có thể giúp gì cho tôi trong thư viện?'")
        print("   - Tra cứu: 'Sách Deep Learning nằm ở đâu và còn không?'")
        print("   - Gia hạn: 'Tôi là RD2026001, xác nhận gia hạn BK001'")
        print("   - Gõ 'exit' hoặc 'quit' để kết thúc phiên trò chuyện.\n")
        while True:
            try:
                user_input = input("👤 Sinh viên hỏi: ").strip()
                if not user_input or user_input.lower() in ["exit", "quit"]:
                    print("👋 Tạm biệt! Kết thúc phiên trò chuyện.")
                    break
                logs = run_react_agent(user_input, provider, mcp_server)
                save_waterfall_trace(logs)
            except (KeyboardInterrupt, EOFError):
                print("\n👋 Đã thoát phiên tương tác.")
                break
    elif "--all" in sys.argv:
        print("🚀 [TEST SUITE MODE] Kiểm tra 5 Test Cases:")
        completed_count = 0
        todo_count = 0
        all_traces = []
        
        for tc in tests:
            print(f"\n==================================================")
            print(f"🧪 [{tc['id']}] Loại test: {tc['type']} (Độ phức tạp: {tc['complexity']})")
            print(f"📌 Kỳ vọng: {tc['expected_behavior']}")
            
            if tc["question"].strip().startswith("TODO"):
                print(f"⏸️ [CHƯA KÍCH HOẠT - ĐANG LÀ TODO]:")
                print(f"   {tc['question']}")
                print(f"   👉 Hãy mở file 'config/test_cases.json' để viết câu hỏi thực tế cho Test Case này!")
                todo_count += 1
            else:
                logs = run_react_agent(tc["question"], provider, mcp_server)
                all_traces.extend(logs)
                completed_count += 1
                
        print(f"\n==================================================")
        print(f"📊 [KẾT QUẢ TEST SUITE]: Đã thực thi {completed_count}/{len(tests)} Test Cases | {todo_count} Test Cases đang chờ điền câu hỏi (TODO)")
        if all_traces:
            save_waterfall_trace(all_traces)
        print(f"💡 Để trò chuyện trực tiếp từng câu: Chạy 'python src/app.py --interactive'")
    else:
        # Chế độ mặc định khi chỉ gõ 'python src/app.py'
        print("ℹ️ HƯỚNG DẪN SỬ DỤNG CHƯƠNG TRÌNH:")
        print("  1. Chat trực tiếp liên tục:   python src/app.py --interactive")
        print("  2. Chạy toàn bộ Test Cases:    python src/app.py --all\n")
        
        sample_query = tests[1]["question"]
        print(f"--- 🏁 DEMO CHẠY THỬ 1 TEST CASE MẪU (TC02: Tra cứu thư viện) ---")
        logs = run_react_agent(sample_query, provider, mcp_server)
        save_waterfall_trace(logs)
        print("\n💡 Hãy thử ngay lệnh: python src/app.py --interactive để chat trực tiếp!")
