from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import json
from urllib.parse import parse_qs, urlparse

DATA = json.loads((Path(__file__).parent / "dispatch_data.json").read_text())
PAGE_HITS = {}


class Handler(BaseHTTPRequestHandler):
    def send_json(self, status, payload, headers=None):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        if headers:
            for key, value in headers.items():
                self.send_header(key, str(value))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            return self.send_json(200, {"status": "ok", "service": "flasheats-dispatch-api"})

        if parsed.path == "/dispatch/orders":
            params = parse_qs(parsed.query)
            page = max(1, int(params.get("page", [1])[0]))
            page_size = min(200, max(1, int(params.get("page_size", [50])[0])))
            PAGE_HITS[page] = PAGE_HITS.get(page, 0) + 1

            # Classroom behavior: transient failures that should be retried.
            if page == 3 and PAGE_HITS[page] == 1:
                return self.send_json(500, {"error": "temporary upstream failure", "retryable": True})
            if page == 5 and PAGE_HITS[page] == 1:
                return self.send_json(
                    429,
                    {"error": "rate limit exceeded", "retry_after_seconds": 1},
                    {"Retry-After": "1"},
                )

            start = (page - 1) * page_size
            end = start + page_size
            items = DATA[start:end]
            return self.send_json(
                200,
                {
                    "data": items,
                    "page": page,
                    "page_size": page_size,
                    "has_more": end < len(DATA),
                    "total_records": len(DATA),
                },
            )

        if parsed.path.startswith("/dispatch/orders/"):
            order_id = parsed.path.rsplit("/", 1)[-1]
            row = next((x for x in DATA if x["order_id"] == order_id), None)
            if row:
                return self.send_json(200, row)
            return self.send_json(404, {"error": "order not found", "order_id": order_id})

        return self.send_json(404, {"error": "not found"})

    def log_message(self, fmt, *args):
        # Keep pipeline output focused; pipeline logger records retrieval events.
        return


if __name__ == "__main__":
    HTTPServer(("127.0.0.1", 8000), Handler).serve_forever()
