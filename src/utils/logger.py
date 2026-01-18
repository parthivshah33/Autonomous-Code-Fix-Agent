"""Logging system for agent interactions and message history"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from ..config import LOG_FILE, DATA_OUTPUT_DIR


class AgentLogger:
    """Manages logging of agent interactions and message history"""
    
    def __init__(self, log_file: Optional[str] = None):
        self.log_file = Path(log_file or LOG_FILE)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.history: List[Dict[str, Any]] = []
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def log_agent_start(self, agent_name: str, state: Dict[str, Any], iteration: int = 1):
        """Log when an agent starts processing"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event": "agent_start",
            "agent": agent_name,
            "iteration": iteration,
            "state_snapshot": {
                "has_rca_report": state.get("rca_report") is not None,
                "has_fix_plan": state.get("fix_plan") is not None,
                "has_patch_result": state.get("patch_result") is not None,
                "input_file_path": state.get("input_file_path", ""),
                "message_count": len(state.get("messages", []))
            }
        }
        self.history.append(entry)
        return entry
    
    def log_agent_end(self, agent_name: str, output: Dict[str, Any], iteration: int = 1):
        """Log when an agent completes processing"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event": "agent_end",
            "agent": agent_name,
            "iteration": iteration,
            "output": output
        }
        self.history.append(entry)
        return entry
    
    def log_tool_call(self, agent_name: str, tool_name: str, tool_input: Dict[str, Any], 
                     tool_output: Dict[str, Any], iteration: int = 1):
        """Log a tool call made by an agent"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event": "tool_call",
            "agent": agent_name,
            "iteration": iteration,
            "tool": tool_name,
            "input": tool_input,
            "output": tool_output
        }
        self.history.append(entry)
        return entry
    
    def log_message(self, agent_name: str, message_type: str, content: str, iteration: int = 1):
        """Log a message from an agent"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event": "message",
            "agent": agent_name,
            "iteration": iteration,
            "message_type": message_type,
            "content": content
        }
        self.history.append(entry)
        return entry
    
    def save_history(self):
        """Save the complete history to JSON file"""
        output = {
            "session_id": self.session_id,
            "start_time": self.history[0]["timestamp"] if self.history else datetime.now().isoformat(),
            "end_time": datetime.now().isoformat(),
            "total_events": len(self.history),
            "history": self.history
        }
        
        with open(self.log_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        return str(self.log_file.absolute())
    
    def save_final_state(self, state: Dict[str, Any]):
        """Save the final shared memory state"""
        final_state_file = self.log_file.parent / f"final_state_{self.session_id}.json"
        
        # Convert Pydantic models to dict and handle LangChain messages
        state_dict = {}
        for key, value in state.items():
            if key == "messages":
                # Convert LangChain messages to serializable format
                state_dict[key] = [
                    {
                        "type": msg.__class__.__name__,
                        "content": msg.content if hasattr(msg, 'content') else str(msg)
                    }
                    for msg in value
                ]
            elif hasattr(value, 'model_dump'):
                state_dict[key] = value.model_dump()
            elif hasattr(value, 'model_dump_json'):
                state_dict[key] = json.loads(value.model_dump_json())
            elif value is None:
                state_dict[key] = None
            else:
                # Try to serialize, fallback to string if not serializable
                try:
                    json.dumps(value)
                    state_dict[key] = value
                except (TypeError, ValueError):
                    state_dict[key] = str(value)
        
        output = {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "shared_memory": state_dict
        }
        
        with open(final_state_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        return str(final_state_file.absolute())


# Global logger instance
_logger_instance: Optional[AgentLogger] = None


def get_logger() -> AgentLogger:
    """Get or create the global logger instance"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = AgentLogger()
    return _logger_instance


def log_agent_start(agent_name: str, state: Dict[str, Any], iteration: int = 1):
    """Convenience function to log agent start"""
    return get_logger().log_agent_start(agent_name, state, iteration)


def log_agent_end(agent_name: str, output: Dict[str, Any], iteration: int = 1):
    """Convenience function to log agent end"""
    return get_logger().log_agent_end(agent_name, output, iteration)


def log_tool_call(agent_name: str, tool_name: str, tool_input: Dict[str, Any], 
                  tool_output: Dict[str, Any], iteration: int = 1):
    """Convenience function to log tool call"""
    return get_logger().log_tool_call(agent_name, tool_name, tool_input, tool_output, iteration)


def save_logs():
    """Save all logs to file"""
    return get_logger().save_history()


def save_final_state(state: Dict[str, Any]):
    """Save final shared memory state"""
    return get_logger().save_final_state(state)
