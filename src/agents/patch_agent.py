"""Patch Generation Agent implementation"""
from typing import Dict, Any
import json
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from ..config import LLM_MODEL, LLM_TEMPERATURE
from ..graph.state import AgentGraphState, PatchResult, RCAReport, FixPlan
from ..tools.file_tools import read_source_file, apply_patch_and_write
from ..tools.code_tools import verify_code_snippet, validate_python_syntax
from ..utils.logger import log_agent_start, log_agent_end
from ..utils.context import set_target_root_dir


PATCH_AGENT_PROMPT = """You are a Senior DevOps Engineer responsible for fixing production code.
You have received a Root Cause Analysis(RCA) report and a strictly defined fix plan.

Your Objectives:
1. **Verify Context:** Never apply a patch blindly. You must read the current state of the file to ensure the Fix Plan matches reality.
2. **Execute Patch:** Use your available tools to apply the fix.
3. **Safety Protocol:** 
   - You are prohibited from overwriting original files. 
   - Your tools handle the creation of the safe 'fixed_' version automatically. 
   - If a tool reports that a code snippet is missing, stop and re-evaluate; do not force the change.

Available Tools:
- `read_source_file`: Read a source code file to verify its current state
- `verify_code_snippet`: Verify that a code snippet exists in a file before patching
- `apply_patch_and_write`: Apply changes and write to a new file (creates 'fixed_' prefix automatically)
- `validate_python_syntax`: Validate that the generated file has correct Python syntax

Instructions:
- Always read the target file first using `read_source_file` to verify its current state
- For each change in the fix plan, verify the original snippet exists using `verify_code_snippet`
- Apply all changes using `apply_patch_and_write` with the list of changes
- Validate the syntax of the generated file using `validate_python_syntax`
- Your final output must confirm the path of the newly created file.

If the Fix Plan provides code snippets, verify they exist in the file exactly as written before applying changes.
If the tool fails (e.g., snippet not found), analyze the error and try to correct the snippet based on the actual file content you read."""


def patch_generation_node(state: AgentGraphState) -> Dict[str, Any]:
    """
    Patch Generation Agent node: Reads RCA and Fix Plan, applies patches.
    
    Args:
        state: Current graph state
        
    Returns:
        Updated state with patch result
    """
    log_agent_start("Patch Generation Agent", state)
    
    # Set target root directory in context for tools
    target_root_dir = state.get("target_root_dir")
    set_target_root_dir(target_root_dir)
    
    rca_report: RCAReport = state.get("rca_report")
    fix_plan: FixPlan = state.get("fix_plan")
    
    if not fix_plan:
        return {
            "messages": [HumanMessage(content="Error: Fix plan missing")],
            "patch_result": None
        }
    
    if not rca_report:
        return {
            "messages": [HumanMessage(content="Error: RCA report missing")],
            "patch_result": None
        }
    
    # Initialize LLM with tool binding for ReAct pattern
    llm = ChatOpenAI(model=LLM_MODEL, temperature=LLM_TEMPERATURE)
    
    # Bind tools to LLM
    tools = [read_source_file, verify_code_snippet, apply_patch_and_write, validate_python_syntax]
    llm_with_tools = llm.bind_tools(tools)
    
    # Prepare context
    rca_summary = rca_report.root_cause_summary
    fix_plan_summary = fix_plan.fix_summary
    
    # Format changes for the agent
    changes_json = json.dumps([c.model_dump() for c in fix_plan.changes], indent=2)
    
    context_prompt = f"""
Input Context:
- RCA Report Summary: {rca_summary}
- Fix Plan Summary: {fix_plan_summary}

Target Files:
{', '.join(set(c.file_path for c in fix_plan.changes))}

Requested Changes:
{changes_json}

Begin by reading the target file(s) to verify the current state, then apply the changes.
"""
    
    try:
        # Get target file path
        target_file = fix_plan.changes[0].file_path if fix_plan.changes else ""
        
        # Step 1: Read the source file
        file_content_result = read_source_file.invoke(target_file)
        
        if not file_content_result.get("success"):
            return {
                "messages": [HumanMessage(content=f"Failed to read file: {file_content_result.get('error')}")],
                "patch_result": None
            }
        
        file_content = file_content_result["content"]
        
        # Step 2: Verify each change snippet exists
        verified_changes = []
        for change in fix_plan.changes:
            verify_result = verify_code_snippet.invoke({
                "file_content": file_content,
                "original_snippet": change.original_snippet,
                "line_number": change.line_number
            })
            
            if verify_result.get("found"):
                verified_changes.append({
                    "original_snippet": change.original_snippet,
                    "fixed_snippet": change.fixed_snippet,
                    "line_number": change.line_number
                })
        
        if not verified_changes:
            return {
                "messages": [HumanMessage(content="No verified changes to apply")],
                "patch_result": None
            }
        
        # Step 3: Apply patches  
        # apply_patch_and_write takes (original_file_path: str, changes: List[Dict])
        patch_result_tool = apply_patch_and_write.invoke({
            "original_file_path": target_file,
            "changes": verified_changes
        })
        
        if not patch_result_tool.get("success"):
            return {
                "messages": [HumanMessage(content=f"Failed to apply patch: {patch_result_tool.get('error')}")],
                "patch_result": None
            }
        
        output_file = patch_result_tool["output_file"]
        
        # Step 4: Validate syntax
        syntax_result = validate_python_syntax.invoke(output_file)
        
        # Generate structured patch result
        structured_llm = llm.with_structured_output(PatchResult)
        
        patch_result = structured_llm.invoke([
            SystemMessage(content="Summarize the patching job."),
            HumanMessage(content=f"""
Patch applied successfully:
- Original file: {target_file}
- Fixed file: {output_file}
- Changes applied: {patch_result_tool['changes_applied']}/{len(verified_changes)}
- Syntax valid: {syntax_result.get('valid', False)}
- Summary: {patch_result_tool.get('change_log', [])}
""")
        ])
        
        # Override with actual values
        patch_result.original_file = target_file
        patch_result.fixed_file = output_file
        patch_result.status = "Success" if patch_result_tool.get("success") else "Failed"
        patch_result.applied_changes_summary = f"Applied {patch_result_tool['changes_applied']} change(s)"
        patch_result.verification_status = "Syntax valid" if syntax_result.get("valid") else "Syntax validation failed"
        
        log_agent_end("Patch Generation Agent", {"patch_result": patch_result.model_dump()})
        
        return {
            "messages": [HumanMessage(content=f"Patch applied: {output_file}")],
            "patch_result": patch_result
        }
        
    except Exception as e:
        import traceback
        error_msg = f"Patch Generation Agent error: {str(e)}\n{traceback.format_exc()}"
        return {
            "messages": [HumanMessage(content=error_msg)],
            "patch_result": None
        }
