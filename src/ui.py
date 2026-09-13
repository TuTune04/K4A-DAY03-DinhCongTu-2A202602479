"""Giao diện web tối giản cho VinUni Library ReAct Agent."""

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import run_react_agent, save_waterfall_trace
from mcp_server import MCPAcademicServer
from providers import get_llm_provider


HTML = r"""<!doctype html>
<html lang="vi">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>VinUni Library Agent</title>
  <style>
    :root{color-scheme:light;--ink:#172033;--muted:#667085;--line:#e4e7ec;--brand:#3157d5;--soft:#f4f6fb}
    *{box-sizing:border-box}body{margin:0;background:var(--soft);color:var(--ink);font:15px/1.5 system-ui,-apple-system,sans-serif}
    main{width:min(820px,100%);height:100vh;margin:auto;padding:20px;display:grid;grid-template-rows:auto 1fr auto;gap:14px}
    header,.composer,.panel{background:#fff;border:1px solid var(--line);border-radius:16px}
    header{padding:16px 18px;display:flex;align-items:center;justify-content:space-between;gap:14px}
    h1{font-size:18px;margin:0}.sub{color:var(--muted);font-size:13px}.status{white-space:nowrap;color:#18794e;font-size:13px}
    #chat{overflow:auto;padding:6px 2px;display:flex;flex-direction:column;gap:12px}
    .msg{max-width:82%;padding:11px 14px;border-radius:15px;white-space:pre-wrap}
    .user{align-self:flex-end;background:var(--brand);color:#fff;border-bottom-right-radius:4px}
    .agent{align-self:flex-start;background:#fff;border:1px solid var(--line);border-bottom-left-radius:4px}
    details{align-self:flex-start;max-width:92%;color:var(--muted);font-size:13px}
    pre{overflow:auto;background:#111827;color:#d1fae5;padding:12px;border-radius:10px;font-size:12px}
    .composer{padding:10px;display:flex;gap:9px}
    textarea{flex:1;resize:none;border:0;outline:0;font:inherit;min-height:44px;padding:10px;background:transparent}
    button{border:0;border-radius:11px;padding:0 18px;background:var(--brand);color:white;font-weight:650;cursor:pointer}
    button:disabled{opacity:.55;cursor:wait}.hint{text-align:center;color:var(--muted);font-size:12px;margin-top:-7px}
    @media(max-width:600px){main{padding:10px}.msg{max-width:92%}.status{display:none}}
  </style>
</head>
<body><main>
  <header><div><h1>📚 VinUni Library Agent</h1><div class="sub">Tra cứu và gia hạn tài liệu qua MCP</div></div><div class="status">● <span id="provider">Đang kết nối</span></div></header>
  <section id="chat"><div class="msg agent">Xin chào! Tôi có thể giúp bạn tìm sách, kiểm tra tình trạng và gia hạn tài liệu.</div></section>
  <div><form class="composer" id="form"><textarea id="input" placeholder="Ví dụ: Tra cứu sách Deep Learning" required></textarea><button id="send">Gửi</button></form><div class="hint">Enter để gửi · Shift Enter để xuống dòng</div></div>
</main><script>
const chat=document.querySelector('#chat'), input=document.querySelector('#input'), send=document.querySelector('#send');
function message(text,kind){const el=document.createElement('div');el.className='msg '+kind;el.textContent=text;chat.appendChild(el);chat.scrollTop=chat.scrollHeight;return el}
fetch('/api/health').then(r=>r.json()).then(x=>document.querySelector('#provider').textContent=x.provider+' · MCP sẵn sàng').catch(()=>document.querySelector('#provider').textContent='Mất kết nối');
document.querySelector('#form').addEventListener('submit',async e=>{e.preventDefault();const query=input.value.trim();if(!query)return;message(query,'user');input.value='';send.disabled=true;const waiting=message('Đang xử lý…','agent');try{const r=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({query})});const data=await r.json();if(!r.ok)throw new Error(data.error||'Không thể xử lý');waiting.textContent=data.answer;const d=document.createElement('details');const s=document.createElement('summary');s.textContent='Xem '+data.trace.length+' bước xử lý';const p=document.createElement('pre');p.textContent=JSON.stringify(data.trace,null,2);d.append(s,p);chat.appendChild(d)}catch(err){waiting.textContent='Lỗi: '+err.message}finally{send.disabled=false;input.focus();chat.scrollTop=chat.scrollHeight}});
input.addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();document.querySelector('#form').requestSubmit()}});
</script></body></html>"""


PROVIDER = get_llm_provider()
MCP_SERVER = MCPAcademicServer()


class AgentUIHandler(BaseHTTPRequestHandler):
    def send_data(self, status, content_type, payload):
        body = payload.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/":
            self.send_data(200, "text/html", HTML)
        elif self.path == "/api/health":
            payload = json.dumps({
                "status": "ok",
                "provider": PROVIDER.__class__.__name__,
                "mcp_server": MCP_SERVER.server_name
            }, ensure_ascii=False)
            self.send_data(200, "application/json", payload)
        else:
            self.send_data(404, "application/json", '{"error":"Not found"}')

    def do_POST(self):
        if self.path != "/api/chat":
            self.send_data(404, "application/json", '{"error":"Not found"}')
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            request = json.loads(self.rfile.read(length).decode("utf-8"))
            query = str(request.get("query", "")).strip()
            if not query:
                raise ValueError("Câu hỏi không được để trống.")
            if len(query) > 2000:
                raise ValueError("Câu hỏi dài tối đa 2000 ký tự.")

            trace = run_react_agent(query, PROVIDER, MCP_SERVER)
            save_waterfall_trace(trace)
            final_events = [e for e in trace if e.get("action_type") == "FINAL_ANSWER"]
            answer = final_events[-1].get("output", "Không có câu trả lời.") if final_events else "Không có câu trả lời."
            payload = json.dumps({"answer": answer, "trace": trace}, ensure_ascii=False)
            self.send_data(200, "application/json", payload)
        except (ValueError, json.JSONDecodeError) as exc:
            self.send_data(400, "application/json", json.dumps({"error": str(exc)}, ensure_ascii=False))
        except Exception as exc:
            self.send_data(500, "application/json", json.dumps({"error": str(exc)}, ensure_ascii=False))

    def log_message(self, format, *args):
        return


if __name__ == "__main__":
    host = "127.0.0.1"
    port = int(os.getenv("UI_PORT", "8000"))
    print(f"📚 Library Agent UI: http://{host}:{port}")
    print(f"🔌 Provider: {PROVIDER.__class__.__name__} | MCP: {MCP_SERVER.server_name}")
    try:
        ThreadingHTTPServer((host, port), AgentUIHandler).serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Đã dừng giao diện.")
