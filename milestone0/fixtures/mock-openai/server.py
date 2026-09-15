from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hashlib
import json
import os
import time


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")
            return
        self.send_error(404)

    def do_POST(self):
        if self.path in ("/v1/embeddings", "/embeddings"):
            length = int(self.headers.get("content-length", "0"))
            request = json.loads(self.rfile.read(length) or b"{}")
            values = request.get("input", [])
            if isinstance(values, str):
                values = [values]
            data = []
            for index, value in enumerate(values):
                digest = hashlib.sha256(str(value).encode()).digest()
                vector = [round((byte - 127.5) / 127.5, 8) for byte in digest[:8]]
                norm = sum(component * component for component in vector) ** 0.5 or 1.0
                data.append(
                    {
                        "object": "embedding",
                        "index": index,
                        "embedding": [component / norm for component in vector],
                    }
                )
            body = {
                "object": "list",
                "model": request.get("model", "admission-deterministic-8"),
                "data": data,
                "usage": {"prompt_tokens": len(values), "total_tokens": len(values)},
            }
            encoded = json.dumps(body).encode()
            self.send_response(200)
            self.send_header("content-type", "application/json")
            self.send_header("content-length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)
            return
        if self.path not in ("/v1/chat/completions", "/chat/completions"):
            self.send_error(404)
            return
        length = int(self.headers.get("content-length", "0"))
        request = json.loads(self.rfile.read(length) or b"{}")
        mode = os.environ.get("MOCK_MODE", "success")
        if mode == "fail":
            self.send_response(503)
            self.send_header("content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": {"message": "injected upstream loss", "type": "service_unavailable"}}).encode())
            return
        if mode == "slow":
            time.sleep(float(os.environ.get("MOCK_DELAY_SECONDS", "5")))
        body = {
            "id": "chatcmpl-admission",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": request.get("model", "mock"),
            "choices": [{"index": 0, "message": {"role": "assistant", "content": "fallback-ok"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 7, "completion_tokens": 3, "total_tokens": 10},
        }
        encoded = json.dumps(body).encode()
        self.send_response(200)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, format, *args):
        print(format % args, flush=True)


ThreadingHTTPServer(("0.0.0.0", int(os.environ.get("PORT", "8080"))), Handler).serve_forever()
