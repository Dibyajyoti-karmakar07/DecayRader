import os
import json
import logging
import asyncio
from google import genai
from google.genai import types
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Run the async agent synchronously for Streamlit compatibility
def run_mcp_agent_sync(prompt: str, model_name="gemini-3.1-flash-lite"):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    try:
        # Hackathon fix: Prevent indefinite hangs with a 45-second timeout
        return loop.run_until_complete(asyncio.wait_for(run_mcp_agent(prompt, model_name), timeout=45.0))
    except asyncio.TimeoutError:
        logger.error("MCP Agent Timeout: Generation took longer than 45 seconds.")
        return "⚠️ The agent took too long to respond (timeout). Please try again or simplify your request."
    except Exception as e:
        logger.error(f"MCP Agent Sync Error: {e}")
        return "⚠️ An unexpected error occurred while gathering intelligence. Please try again."


async def run_mcp_agent(prompt: str, model_name="gemini-3.1-flash-lite"):
    load_dotenv()
    uri = os.getenv("MONGODB_URI")
    if not uri:
        logger.error("MONGODB_URI not set")
        return None
        
    # Hackathon fix: Streamlit Cloud permission workaround for npx cache
    safe_env = os.environ.copy()
    safe_env["npm_config_cache"] = "/tmp/.npm"
    
    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "mongodb-mcp-server", uri],
        env=safe_env
    )
    
    api_key = os.getenv("GEMINI_API_KEY")
    gemini_client = genai.Client(api_key=api_key)
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # Fetch tools from MCP server
                tools_response = await session.list_tools()
                
                function_declarations = []
                mcp_tool_names = {}
                for t in tools_response.tools:
                    gemini_name = t.name.replace("-", "_")
                    mcp_tool_names[gemini_name] = t.name
                    
                    props = {}
                    req = []
                    if hasattr(t, "inputSchema") and isinstance(t.inputSchema, dict):
                        props = t.inputSchema.get("properties", {})
                        req = t.inputSchema.get("required", [])
                    
                    simplified_props = {}
                    for k, v in props.items():
                        simplified_props[k] = {"type": "STRING", "description": str(v.get("description", ""))}
                        
                    func_decl = {
                        "name": gemini_name,
                        "description": str(t.description or "")[:1000],
                        "parameters": {
                            "type": "OBJECT",
                            "properties": simplified_props,
                            "required": req
                        }
                    }
                    function_declarations.append(func_decl)
                    
                gemini_tools = [{"function_declarations": function_declarations}]
                
                chat = gemini_client.chats.create(
                    model=model_name,
                    config={"tools": gemini_tools, "temperature": 0.2}
                )
                
                logger.info("Sending initial prompt to Gemini with MCP Tools...")
                response = chat.send_message(prompt)
                
                turn = 0
                max_turns = 8 # Prevent infinite loops
                while turn < max_turns:
                    turn += 1
                    
                    if not response.function_calls:
                        logger.info("No more function calls. Returning text.")
                        break
                        
                    parts = []
                    for fc in response.function_calls:
                        gemini_name = fc.name
                        mcp_name = mcp_tool_names.get(gemini_name)
                        if mcp_name:
                            # Extract args
                            args = {}
                            if fc.args:
                                for k, v in fc.args.items():
                                    try:
                                        # Convert string back to dict if needed since we told Gemini it's a string
                                        args[k] = json.loads(v) if isinstance(v, str) and (v.startswith("{") or v.startswith("[")) else v
                                    except:
                                        args[k] = v
                                        
                            try:
                                logger.info(f"Executing MCP tool {mcp_name} with args {args}")
                                mcp_result = await session.call_tool(mcp_name, arguments=args)
                                
                                text_content = ""
                                if hasattr(mcp_result, "content"):
                                    for c in mcp_result.content:
                                        if getattr(c, "type", "text") == "text":
                                            text_content += getattr(c, "text", "") + "\n"
                                
                                # Prevent massive context overflow
                                text_content = text_content[:20000]
                                if not text_content:
                                    text_content = "Success, but no text content returned."
                                            
                                parts.append(
                                    types.Part.from_function_response(
                                        name=gemini_name,
                                        response={"result": text_content}
                                    )
                                )
                            except Exception as e:
                                logger.error(f"Error calling {mcp_name}: {e}")
                                parts.append(
                                    types.Part.from_function_response(
                                        name=gemini_name,
                                        response={"error": str(e)}
                                    )
                                )
                        else:
                            parts.append(
                                types.Part.from_function_response(
                                    name=gemini_name,
                                    response={"error": f"Unknown tool {gemini_name}"}
                                )
                            )
                    
                    if parts:
                        response = chat.send_message(parts)
                    else:
                        break
                
                return response.text
    except Exception as e:
        logger.error(f"MCP Agent Error: {e}")
        return None
