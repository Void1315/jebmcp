# -*- coding: utf-8 -*-
"""
JEB MCP Plugin - Optimized and reliable version
"""
import json
import threading
import traceback
import BaseHTTPServer

from com.pnfsoftware.jeb.client.api import IScript, IGraphicalClientContext
from javax.swing import JFrame, JLabel, JButton, JPanel
from java.awt import BorderLayout, Color, Font
from java.awt.event import ActionListener, WindowAdapter
from java.lang import Runnable, Thread

from core.project_manager import ProjectManager
from core.jeb_operations import JebOperations
from api.jsonrpc_handler import JSONRPCHandler


class JSONRPCError(Exception):
    """JSON-RPC error with code and message"""
    def __init__(self, code, message, data=None):
        super(JSONRPCError, self).__init__(message)
        self.code = code
        self.message = message
        self.data = data


class JSONRPCRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    """HTTP handler for JSON-RPC requests"""

    def do_POST(self):
        if self.path != "/mcp":
            return self._send_error(-32098, "Invalid endpoint")

        try:
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length == 0:
                return self._send_error(-32700, "Missing request body")

            request = json.loads(self.rfile.read(content_length))
            response = self._handle_request(request)
        except ValueError:
            return self._send_error(-32700, "Invalid JSON")
        except Exception as e:
            traceback.print_exc()
            return self._send_error(-32603, "Internal error", traceback.format_exc())

        self._send_response(response)

    def _handle_request(self, request):
        """Process JSON-RPC request and return response"""
        response = {"jsonrpc": "2.0", "id": request.get("id")}

        try:
            if request.get("jsonrpc") != "2.0":
                raise JSONRPCError(-32600, "Invalid JSON-RPC version")
            if "method" not in request:
                raise JSONRPCError(-32600, "Method not specified")

            handler = getattr(self.server, 'rpc_handler', None)
            if not handler:
                raise JSONRPCError(-32603, "RPC handler not initialized")

            result = handler.handle_request(request["method"], request.get("params", []))
            response["result"] = result

        except JSONRPCError as e:
            response["error"] = {"code": e.code, "message": e.message}
            if e.data:
                response["error"]["data"] = e.data

        return response

    def _send_response(self, data):
        """Send JSON response"""
        body = json.dumps(data).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_error(self, code, message, data=None):
        """Send JSON-RPC error response"""
        error = {"code": code, "message": message}
        if data:
            error["data"] = data
        self._send_response({"jsonrpc": "2.0", "error": error})

    def log_message(self, format, *args):
        pass


class MCPServer(object):
    """HTTP server for MCP plugin"""
    
    HOST = "127.0.0.1"
    PORT = 16161

    def __init__(self, rpc_handler):
        if not rpc_handler:
            raise ValueError("RPC handler required")
        
        self.rpc_handler = rpc_handler
        self.server = None
        self.thread = None
        self.running = False
        self.start_error = None

    def start(self):
        """Start HTTP server in background thread"""
        if self.running:
            return True

        self.running = True
        self.start_error = None
        self.thread = threading.Thread(target=self._run)
        self.thread.daemon = True
        self.thread.start()
        
        # Wait a moment to detect immediate startup errors
        import time
        time.sleep(0.1)
        
        return self.start_error is None

    def stop(self):
        """Stop HTTP server"""
        if not self.running:
            return

        self.running = False
        if self.server:
            try:
                self.server.shutdown()
                self.server.server_close()
            except:
                pass
        if self.thread:
            self.thread.join(timeout=2.0)
        
        self.server = None
        print("[MCP] Server stopped")

    def _run(self):
        """Run HTTP server"""
        try:
            self.server = BaseHTTPServer.HTTPServer(
                (self.HOST, self.PORT), 
                JSONRPCRequestHandler
            )
            self.server.rpc_handler = self.rpc_handler
            print("[MCP] Server started at http://{0}:{1}".format(self.HOST, self.PORT))
            self.server.serve_forever()
        except Exception as e:
            if hasattr(e, 'errno') and e.errno in (98, 10048):
                print("[MCP] Error: Port {0} already in use".format(self.PORT))
            else:
                print("[MCP] Server error: {0}".format(e))
            self.start_error = e
            self.running = False


class MCPPlugin(object):
    """Main MCP plugin controller"""
    
    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self.server = None
        self.ui_frame = None

    @classmethod
    def get_instance(cls):
        """Get or create singleton instance"""
        with cls._lock:
            if cls._instance is None:
                cls._instance = MCPPlugin()
            return cls._instance
    
    @classmethod
    def reset_instance(cls):
        """Reset singleton for clean restart"""
        with cls._lock:
            cls._instance = None

    def start(self, ctx):
        """Initialize and start MCP plugin"""
        if self.server and self.server.running:
            print("[MCP] Server already running")
            return True
            
        try:
            project_mgr = ProjectManager(ctx)
            jeb_ops = JebOperations(project_mgr, ctx)
            rpc_handler = JSONRPCHandler(jeb_ops)
            
            self.server = MCPServer(rpc_handler)
            success = self.server.start()
            
            if success:
                print("[MCP] Plugin started successfully")
            else:
                print("[MCP] Failed to start server")
            
            return success
            
        except Exception as e:
            print("[MCP] Error: {0}".format(e))
            traceback.print_exc()
            return False

    def stop(self):
        """Stop MCP plugin and cleanup"""
        # Close UI first
        if self.ui_frame:
            try:
                self.ui_frame.dispose()
            except:
                pass
            self.ui_frame = None
        
        # Stop server
        if self.server:
            self.server.stop()
            self.server = None
        
        print("[MCP] Plugin terminated")


class MCP(IScript):
    """JEB script entry point"""

    def run(self, ctx):
        plugin = MCPPlugin.get_instance()
        
        # Try to start server
        if not plugin.start(ctx):
            print("[MCP] Cannot start: server initialization failed")
            return

        # Show UI or wait for console input
        if isinstance(ctx, IGraphicalClientContext):
            self._show_ui(plugin)
        else:
            print("[MCP] Press Enter to stop")
            try:
                raw_input()
            finally:
                plugin.stop()

    def _show_ui(self, plugin):
        """Show control UI in graphical mode"""
        # If UI already exists, bring to front
        if plugin.ui_frame:
            try:
                plugin.ui_frame.toFront()
                plugin.ui_frame.requestFocus()
                print("[MCP] UI window focused")
                return
            except:
                plugin.ui_frame = None
        
        # Create new UI
        class UIRunnable(Runnable):
            def __init__(self, plugin_ref):
                self.plugin = plugin_ref

            def run(self):
                frame = JFrame(u"JEB MCP Service")
                frame.setSize(450, 150)
                frame.setDefaultCloseOperation(JFrame.DISPOSE_ON_CLOSE)
                frame.setLocationRelativeTo(None)
                
                self.plugin.ui_frame = frame

                # Status label
                status = JLabel(
                    u"<html><center>"
                    u"<b><font color='green' size='5'>● MCP Server Running</font></b><br>"
                    u"<font size='3'>http://127.0.0.1:16161/mcp</font><br>"
                    u"<font size='2'>Close window to stop service</font>"
                    u"</center></html>"
                )
                status.setHorizontalAlignment(JLabel.CENTER)
                frame.add(status, BorderLayout.CENTER)

                # Stop button
                plugin_ref = self.plugin
                
                class StopListener(ActionListener):
                    def actionPerformed(self, e):
                        plugin_ref.stop()

                stop_btn = JButton(u"Stop Server")
                stop_btn.addActionListener(StopListener())
                stop_btn.setBackground(Color(255, 100, 100))
                stop_btn.setForeground(Color.WHITE)
                stop_btn.setFont(Font("Arial", Font.BOLD, 13))
                frame.add(stop_btn, BorderLayout.SOUTH)

                # Window listeners
                class WindowListener(WindowAdapter):
                    def windowClosing(self, e):
                        plugin_ref.stop()
                    
                    def windowClosed(self, e):
                        plugin_ref.ui_frame = None

                frame.addWindowListener(WindowListener())
                frame.setVisible(True)

        Thread(UIRunnable(plugin)).start()