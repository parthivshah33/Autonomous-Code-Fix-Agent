"""LangGraph workflow definition"""
from typing import Optional
from langgraph.graph import StateGraph, START, END

from .state import AgentGraphState
from ..agents.rca_agent import rca_agent_node
from ..agents.fix_agent import fix_suggestion_node
from ..agents.patch_agent import patch_generation_node


def build_workflow():
    """
    Builds and compiles the LangGraph workflow.
    
    Returns:
        Compiled graph ready for execution
    """
    # Initialize State Graph
    workflow = StateGraph(AgentGraphState)

    # Add Nodes
    workflow.add_node("rca_node", rca_agent_node)
    workflow.add_node("fix_suggestion_node", fix_suggestion_node)
    workflow.add_node("patch_generation_node", patch_generation_node)

    # Define Edges (Linear Pipeline)
    # Entry Point -> RCA
    workflow.add_edge(START, "rca_node")

    # RCA -> Fix Suggestion
    workflow.add_edge("rca_node", "fix_suggestion_node")

    # Fix Suggestion -> Patch Generation
    workflow.add_edge("fix_suggestion_node", "patch_generation_node")

    # Patch Generation -> End
    workflow.add_edge("patch_generation_node", END)

    # Compile and return
    return workflow.compile()


def create_initial_state(input_file_path: str, target_root_dir: Optional[str] = None) -> AgentGraphState:
    """
    Creates the initial state for the graph.
    
    Args:
        input_file_path: Path to the error log file
        target_root_dir: Root directory of the target codebase being fixed
        
    Returns:
        Initial AgentGraphState
    """
    return {
        "input_file_path": input_file_path,
        "target_root_dir": target_root_dir,
        "messages": [],
        "rca_report": None,
        "fix_plan": None,
        "patch_result": None
    }
