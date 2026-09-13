"""
🔌 MODEL CONTEXT PROTOCOL (MCP) SERVER MODULE
Mô phỏng kiến trúc MCP Server (Client-Server Architecture) cung cấp công cụ chuẩn hóa.
"""

import json
import sys
from typing import Dict, Any, List
from tools import TOOLS_SCHEMA, dispatch_tool_call

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

class MCPAcademicServer:
    """
    Giả lập MCP Server tuân thủ chuẩn giao thức Model Context Protocol
    """
    def __init__(self, server_name: str = "vinuni-library-mcp-server"):
        self.server_name = server_name
        self.version = "2026.1.0"
        
    def list_tools(self) -> List[Dict[str, Any]]:
        """Trả về danh sách các Tools chuẩn giao thức MCP"""
        return TOOLS_SCHEMA
        
    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Thực thi Tool qua execution layer và đóng gói kết quả theo JSON-RPC 2.0.
        """
        result_json = dispatch_tool_call(tool_name, arguments)
        content = json.loads(result_json)

        return {
            "jsonrpc": "2.0",
            "server": self.server_name,
            "tool": tool_name,
            "result": content
        }


if __name__ == "__main__":
    print("==========================================================")
    print("🔌 KIỂM THỬ ĐỘC LẬP MCP SERVER (vinuni-library-mcp-server)")
    print("==========================================================")
    
    server = MCPAcademicServer()
    tools = server.list_tools()
    print(f"✅ Khởi tạo thành công MCP Server: {server.server_name} (Version: {server.version})")
    print(f"📦 Số lượng Tools công bố: {len(tools)}")
    
    # Kiểm tra trạng thái Tool Schemas
    renew_tool = next((t for t in tools if t.get("name") == "renew_library_loan"), None)
    if not renew_tool or not renew_tool.get("parameters", {}).get("properties"):
        print("⏳ [TASK 1.2]: Tool 'renew_library_loan' chưa có schema đầy đủ trong 'src/tools.py'.")
    else:
        print("✅ [TASK 1.2]: Tool 'renew_library_loan' đã có schema đầy đủ.")

    # Kiểm tra trạng thái Task 2.1 (call_tool)
    test_result = server.call_tool("library_query", {"query": "Deep Learning"})
    if not test_result:
        print("⏳ [TASK 2.1]: Hàm call_tool() đang trả về rỗng.")
    else:
        print("✅ [TASK 2.1]: Test dispatch tool 'library_query' thành công:")
        print(f"   Phản hồi JSON-RPC: {json.dumps(test_result, ensure_ascii=False)}")
