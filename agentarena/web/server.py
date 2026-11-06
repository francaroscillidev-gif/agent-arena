import http.server
import socketserver
import json
import urllib.parse
import os
from agentarena.core.storage import RunStorage
from agentarena.core.harness import AgentHarness
from agentarena.core.mock_agents import MockLegacyAgent, MockOptimizedAgent
from agentarena.tasks.benchmarks import get_standard_tasks

PORT = 8080
STORAGE = RunStorage(runs_dir="runs")
HARNESS = AgentHarness(storage=STORAGE)
STATIC_DIR = os.path.dirname(__file__)

class AgentArenaHTTPHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        super().end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            with open(os.path.join(STATIC_DIR, "index.html"), "rb") as f:
                self.wfile.write(f.read())
            return

        elif path == "/api/versions":
            versions = STORAGE.list_versions()
            self._send_json({"versions": versions})
            return

        elif path.startswith("/api/runs/"):
            version = urllib.parse.unquote(path.replace("/api/runs/", ""))
            runs = STORAGE.load_runs_for_version(version)
            self._send_json({"version": version, "runs": runs})
            return

        elif path.startswith("/api/summary/"):
            version = urllib.parse.unquote(path.replace("/api/summary/", ""))
            summary = STORAGE.get_version_summary(version)
            self._send_json(summary)
            return

        elif path == "/api/tasks":
            tasks = [t.__dict__ for t in get_standard_tasks()]
            self._send_json({"tasks": tasks})
            return

        else:
            self.send_error(404, "Endpoint Not Found")

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/run-benchmark":
            query = urllib.parse.parse_qs(parsed.query)
            agent_type = query.get("type", ["baseline"])[0]

            tasks = get_standard_tasks()
            if agent_type == "baseline":
                agent = MockLegacyAgent()
            else:
                agent = MockOptimizedAgent()

            trajectories = HARNESS.run_benchmark(agent, tasks)
            self._send_json({
                "status": "success",
                "agent_version": agent.version,
                "tasks_run": len(trajectories),
                "success_count": sum(1 for t in trajectories if t.success)
            })
            return

        else:
            self.send_error(404, "Not Found")

    def _send_json(self, data: dict):
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"))

def serve(port=PORT):
    # Allow port reuse immediately
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", port), AgentArenaHTTPHandler) as httpd:
        print(f"🚀 AgentArena Web UI live on http://localhost:{port}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down AgentArena server.")

if __name__ == "__main__":
    serve()
