"""
MCP Client for discovering and calling tools from an MCP server.
Uses HTTP transport only.
"""
from typing import Dict, List, Optional, Any
import requests


class MCPClient:
    """Client for interacting with MCP servers via HTTP"""
    
    def __init__(self, server_url: str):
        """
        Initialize MCP client
        
        Args:
            server_url: URL of MCP server (e.g., http://localhost:8000)
        """
        if not server_url:
            raise ValueError("Server URL must be provided")
        
        self.server_url = server_url
        self.tools_cache: Dict[str, Any] = {}
    
    def _send_http_request(self, endpoint: str, payload: Dict = None, method: str = "POST") -> Dict:
        """Send request via HTTP transport"""
        try:
            url = f"{self.server_url.rstrip('/')}/{endpoint.lstrip('/')}"
            if method.upper() == "GET":
                response = requests.get(url, timeout=10)
            else:
                response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            
            # Handle both JSON and plain text responses
            content_type = response.headers.get("content-type", "").lower()
            if "application/json" in content_type:
                return response.json()
            else:
                # Return plain text as a dict with content key
                return {"content": response.text}
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error communicating with MCP server: {str(e)}")
        except ValueError as e:
            # JSON decode error - try to return as text
            return {"content": response.text}
    
    def discover_tools(self) -> List[Dict]:
        """
        Discover available tools from the MCP server by fetching OpenAPI specification.
        FastAPI/FastMCP automatically generates OpenAPI spec at /openapi.json.
        
        Returns:
            List of available tools with their schemas
        """
        try:
            # Primary method: Use OpenAPI spec (FastAPI/FastMCP provides this automatically)
            print(f"Discovering tools from OpenAPI specification at {self.server_url}/openapi.json...")
            try:
                tools = self._discover_from_openapi()
                if tools:
                    self.tools_cache = {tool.get("name", ""): tool for tool in tools}
                    print(f"✅ Successfully discovered {len(tools)} tools from OpenAPI spec")
                    return tools
            except Exception as e:
                print(f"❌ OpenAPI discovery failed: {e}")
            
            # Fallback: Try MCP standard discovery endpoint (if server supports it)
            print("Falling back to MCP standard discovery endpoint...")
            try:
                tools = self._discover_from_mcp_endpoint()
                if tools:
                    self.tools_cache = {tool.get("name", ""): tool for tool in tools}
                    print(f"✅ Successfully discovered {len(tools)} tools via MCP standard endpoint")
                    return tools
            except Exception as e:
                print(f"   MCP standard endpoint not available: {e}")
            
            print("⚠️  No tools discovered using any method")
            return []
        except Exception as e:
            print(f"Error discovering tools: {e}")
            return []
    
    def _discover_from_mcp_endpoint(self) -> List[Dict]:
        """
        Try to discover tools using MCP standard discovery endpoint (tools/list)
        This is the standard MCP protocol method if the server supports it
        """
        endpoints_to_try = [
            ("POST", "mcp/tools/list", {}),
            ("POST", "tools/list", {"method": "tools/list"}),
            ("GET", "mcp/tools/list", None),
            ("GET", "tools/list", None),
        ]
        
        for method, endpoint, payload in endpoints_to_try:
            try:
                result = self._send_http_request(endpoint, payload, method)
                
                # MCP standard response format
                if isinstance(result, dict):
                    # Try MCP standard response format: { "tools": [...] }
                    tools = result.get("tools")
                    if tools and isinstance(tools, list):
                        return tools
                    
                    # Try alternative formats
                    tools = (result.get("result", {}).get("tools") or
                            result.get("data") or
                            result.get("items"))
                    if tools and isinstance(tools, list):
                        return tools
                        
                elif isinstance(result, list):
                    # Direct list of tools
                    return result
                    
            except Exception as e:
                continue
        
        raise Exception("MCP standard discovery endpoint not available")
    
    def _discover_from_openapi(self) -> List[Dict]:
        """
        Discover tools by fetching and parsing OpenAPI specification.
        FastAPI/FastMCP automatically generates this at /openapi.json
        
        Returns:
            List of discovered tools with complete schemas
        """
        try:
            # Fetch OpenAPI spec
            openapi_url = f"{self.server_url.rstrip('/')}/openapi.json"
            print(f"   Fetching OpenAPI spec from {openapi_url}...")
            response = requests.get(openapi_url, timeout=10)
            response.raise_for_status()
            openapi_spec = response.json()
            
            tools = []
            paths = openapi_spec.get("paths", {})
            
            print(f"   Found {len(paths)} endpoints in OpenAPI spec")
            
            # Extract all endpoints from OpenAPI spec
            for path, path_item in paths.items():
                # Process each HTTP method (POST, GET, etc.)
                for method, operation in path_item.items():
                    if method.lower() not in ["post", "get", "put", "patch", "delete"]:
                        continue
                    
                    # Focus on MCP tool endpoints (usually under /mcp/)
                    # Also include any POST endpoints as they're likely tool calls
                    is_mcp_endpoint = "/mcp/" in path.lower()
                    is_post_endpoint = method.lower() == "post"
                    
                    if is_mcp_endpoint or (is_post_endpoint and path != "/"):
                        # Extract tool information
                        tool_name, original_path = self._extract_tool_info_from_path(path)
                        
                        # Get operation details
                        summary = operation.get("summary", "")
                        description = operation.get("description", "")
                        operation_id = operation.get("operationId", "")
                        
                        # Extract input schema from request body or parameters
                        properties = {}
                        required = []
                        
                        # Try to get schema from request body (POST/PUT)
                        request_body = operation.get("requestBody", {})
                        if request_body:
                            properties, required = self._extract_schema_from_request_body(request_body)
                        
                        # Try to get schema from parameters (GET/query params)
                        parameters = operation.get("parameters", [])
                        if parameters and not properties:
                            properties, required = self._extract_schema_from_parameters(parameters)
                        
                        # Create tool definition
                        tool = {
                            "name": tool_name,
                            "description": description or summary or f"Tool at {path} ({method.upper()})",
                            "inputSchema": {
                                "type": "object",
                                "properties": properties,
                                "required": required
                            },
                            "_endpoint_path": original_path,  # Store original path for calling
                            "_http_method": method.upper(),   # Store HTTP method
                            "_operation_id": operation_id      # Store operation ID
                        }
                        tools.append(tool)
                        print(f"   ✓ Discovered tool: {tool_name} ({method.upper()} {path})")
            
            if not tools:
                print("   ⚠️  No MCP tools found in OpenAPI spec")
            
            return tools
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to fetch OpenAPI spec: {e}")
        except Exception as e:
            raise Exception(f"Error parsing OpenAPI spec: {e}")
    
    def _extract_tool_info_from_path(self, path: str) -> tuple:
        """
        Extract tool name and endpoint path from OpenAPI path
        
        Returns:
            (tool_name, original_path)
        """
        path_parts = path.strip("/").split("/")
        original_path = path.strip("/")
        
        # Extract tool name from last path segment
        last_part = path_parts[-1] if path_parts else ""
        
        # For MCP endpoints like /mcp/read_file_mcp, extract "readfilemcp"
        if "/mcp/" in path.lower():
            tool_name = last_part.replace("_", "").replace("-", "")
        else:
            # For other endpoints, use the last segment
            tool_name = last_part.replace("/", "_").replace("-", "_")
        
        return tool_name, original_path
    
    def _extract_schema_from_request_body(self, request_body: Dict) -> tuple:
        """Extract properties and required fields from request body"""
        properties = {}
        required = []
        
        if "content" in request_body:
            for content_type, content_spec in request_body["content"].items():
                if "application/json" in content_type or "application/x-www-form-urlencoded" in content_type:
                    schema = content_spec.get("schema", {})
                    if "properties" in schema:
                        properties = schema["properties"]
                    if "required" in schema:
                        required = schema["required"]
                    break
        
        return properties, required
    
    def _extract_schema_from_parameters(self, parameters: List[Dict]) -> tuple:
        """Extract properties and required fields from query/path parameters"""
        properties = {}
        required = []
        
        for param in parameters:
            param_name = param.get("name")
            param_schema = param.get("schema", {})
            param_required = param.get("required", False)
            
            if param_name:
                properties[param_name] = {
                    "type": param_schema.get("type", "string"),
                    "description": param.get("description", "")
                }
                if param_required:
                    required.append(param_name)
        
        return properties, required
    
    def get_tool_info(self, tool_name: str) -> Optional[Dict]:
        """
        Get information about a specific tool
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Tool schema or None if not found
        """
        if not self.tools_cache:
            self.discover_tools()
        
        return self.tools_cache.get(tool_name)
    
    def call_tool(self, tool_name: str, arguments: Dict = None) -> Dict:
        """
        Call a tool on the MCP server
        
        Args:
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool
            
        Returns:
            Result from the tool call
        """
        arguments = arguments or {}
        
        try:
            # Check if we have stored endpoint info from OpenAPI discovery
            tool_info = self.tools_cache.get(tool_name)
            stored_endpoint = None
            stored_method = "POST"  # Default to POST
            
            if tool_info:
                stored_endpoint = tool_info.get("_endpoint_path")
                stored_method = tool_info.get("_http_method", "POST")
            
            # Try endpoints with their correct HTTP methods
            endpoints_to_try = []
            
            # First, try the stored endpoint from OpenAPI (most reliable)
            if stored_endpoint:
                # Use the correct HTTP method from OpenAPI spec
                endpoints_to_try.append((stored_endpoint, arguments, stored_method))
                # Also try POST as fallback if method was different
                if stored_method != "POST":
                    endpoints_to_try.append((stored_endpoint, arguments, "POST"))
            
            # Fallback: Try standard MCP patterns (POST by default)
            endpoints_to_try.extend([
                ("call_tool", {"tool_name": tool_name, "arguments": arguments}, "POST"),
                ("tools/call", {"name": tool_name, "arguments": arguments}, "POST"),
                ("mcp/tools/call", {"name": tool_name, "arguments": arguments}, "POST"),
                (f"tools/{tool_name}", arguments, "POST"),
                (f"invoke/{tool_name}", arguments, "POST"),
                (f"mcp/{tool_name}", arguments, "POST"),
            ])
            
            last_error = None
            for endpoint, payload, method in endpoints_to_try:
                try:
                    result = self._send_http_request(endpoint, payload, method)
                    if result:
                        # Extract content from result
                        if isinstance(result, dict):
                            content = result.get("content", result.get("result", result))
                            if content:  # Only return if we got actual content
                                print(f"Successfully called tool '{tool_name}' via {method} {endpoint}")
                                return content
                        elif result:  # Plain result
                            print(f"Successfully called tool '{tool_name}' via {method} {endpoint}")
                            return result
                except Exception as e:
                    last_error = str(e)
                    print(f"Failed to call via {method} '{endpoint}': {e}")
                    # Continue to next endpoint
                    continue
            
            error_msg = f"Could not call tool '{tool_name}' via HTTP"
            if last_error:
                error_msg += f". Last error: {last_error}"
            raise Exception(error_msg)
        except Exception as e:
            raise Exception(f"Error calling tool '{tool_name}': {str(e)}")
    
    def read_file(self, file_path: str) -> str:
        """
        Convenience method to call the readfile tool
        
        Args:
            file_path: Path to the file to read
            
        Returns:
            File content as string
        """
        try:
            result = self.call_tool("readfile", {"path": file_path})
            
            # Handle different response formats
            if isinstance(result, dict):
                content = result.get("content", result.get("text", result.get("result", "")))
                return content if isinstance(content, str) else str(content)
            elif isinstance(result, str):
                return result
            else:
                return str(result)
        except Exception as e:
            return f"Error reading file: {str(e)}"
    
# Example usage and testing
if __name__ == "__main__":
    # Example: HTTP transport
    # client = MCPClient(server_url="http://localhost:8000")
    
    # Discover tools
    # tools = client.discover_tools()
    # print("Available tools:", [t.get("name") for t in tools])
    
    # Call readfile tool
    # content = client.read_file("/path/to/file.txt")
    # print("File content:", content)
    
    pass

