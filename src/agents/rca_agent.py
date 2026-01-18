"""RCA Agent implementation"""
from typing import Dict, Any
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from ..config import LLM_MODEL, LLM_TEMPERATURE
from ..graph.state import AgentGraphState, RCAReport
from ..tools.rca_tools import get_root_cause_details
from ..utils.context import set_target_root_dir


RCA_PROMPT = """You are a **specialized Root Cause Analysis Agent** tasked with investigating software errors and identifying their underlying causes. Your role is the **first critical step** in a three-agent error resolution pipeline.

---

## Responsibilities

### 1. Analyze Error Data
- Examine the provided stack traces, error messages, and code context.
- Understand what went wrong at a technical level.

### 2. Identify the Root Cause
- Determine the fundamental reason for the error.
- Focus on causes, not just symptoms.

### 3. Locate Affected Code
- Pinpoint the exact **file**, **function**, and **line number** where the issue originates.

### 4. Provide Evidence
- Support findings with concrete references:
  - Stack trace entries
  - Code snippets
  - File paths and line numbers

### 5. Document Your Analysis
- Output a structured, detailed analysis.
- Ensure downstream agents can rely on your findings.

### 6. Severity and Confidence Assessment
- Classify error severity: CRITICAL, HIGH, MEDIUM, or LOW
- Assess confidence in your conclusion: HIGH, MEDIUM, or LOW
- Document assumptions made during analysis
- Note alternative hypotheses you considered but rejected

---

## Input Format:
You will receive error information from the tool with the error file path.
Start every analysis by calling that tool, then proceed with systematic investigation.

This tool returns:
- Error type and message
- Internal code execution flow with stack frames
- Code snippets for each frame
- Full stack trace for reference

## Analysis Process

Follow this systematic approach:

### 1. Error Classification
- Identify the exception type (e.g., `AttributeError`, `TypeError`, `KeyError`)
- Understand what this exception type indicates
- Note any patterns or common causes for this error type

### 2. Stack Trace Analysis
- Review execution flow from the most recent call backwards
- Distinguish between framework/library code and application code
- Focus on internal application frames where the actual bug exists

### 3. Code Context Examination
- Analyze the code snippets provided for each frame
- Look for obvious issues:
  - Typos
  - Incorrect attribute names
  - Wrong variable usage
- Check for logical errors or incorrect assumptions

### 4. Root Cause Identification
Ask yourself:
- What is the immediate cause of the error?  
  (e.g., accessing a non-existent attribute)
- Why did this happen?  
  (e.g., typo in attribute name, wrong model definition)
- Is this a simple typo, a logic error, or a design issue?
- Are there related issues that might stem from the same root cause?
- What are contributing factors? (missing tests, no type checking, unclear naming, etc.)

### 5. Impact Assessment
- Which file(s) are affected?
- Which function(s) contain the bug?
- What is the exact line number of the error?
- Could this error affect other parts of the codebase?
- What related files should be examined? (models, schemas, configs)
- What imports or dependencies are involved?
- Are there database/ORM schema considerations?

---

## Critical Guidelines

### DO
- Be precise and specific in your analysis
- Quote exact code snippets and line numbers
- Explain technical details clearly
- Consider multiple potential causes before settling on the root cause
- Note if the error suggests other potential issues
- Use the provided tools to gather information

### DON'T
- Make assumptions without evidence from the stack trace
- Jump to conclusions without analyzing the full context
- Ignore framework or library context that might be relevant
- Provide vague or generic explanations
- Suggest fixes  
  *(This is the next agent's job — focus only on analysis)*
- Overlook simple solutions in favor of complex ones

---

## Execution Instruction

Begin your analysis by calling the respected tool in order to get the error/exception details for the provided error file path.  
Then proceed with your systematic investigation following the process outlined above."""


def rca_agent_node(state: AgentGraphState) -> Dict[str, Any]:
    """
    RCA Agent node: Analyzes error files and generates RCA report.
    
    Args:
        state: Current graph state
        
    Returns:
        Updated state with RCA report
    """
    from ..utils.logger import log_agent_start, log_agent_end, log_tool_call
    
    log_agent_start("RCA Agent", state)
    
    # Set target root directory in context for tools
    target_root_dir = state.get("target_root_dir")
    set_target_root_dir(target_root_dir)
    
    input_file_path = state.get("input_file_path", "")
    
    if not input_file_path:
        return {
            "messages": [HumanMessage(content="Error: No input file path provided")],
            "rca_report": None
        }
    
    # Initialize LLM
    llm = ChatOpenAI(model=LLM_MODEL, temperature=LLM_TEMPERATURE)
    
    try:
        # Call tool to get error details
        tool_result = get_root_cause_details.invoke(input_file_path)
        
        if "error" in tool_result:
            error_msg = f"RCA Tool error: {tool_result['error']}"
            return {
                "messages": [HumanMessage(content=error_msg)],
                "rca_report": None
            }
        
        # Generate structured RCA report using LLM
        structured_llm = llm.with_structured_output(RCAReport)
        
        # Combine prompt with tool result
        full_context = RCA_PROMPT + "\n\n" + tool_result.get("llm_prompt_context", str(tool_result))
        
        rca_report = structured_llm.invoke([HumanMessage(content=full_context)])
        
        log_agent_end("RCA Agent", {"rca_report": rca_report.model_dump()})
        
        return {
            "messages": [HumanMessage(content=f"RCA analysis complete. Error: {rca_report.error_type}")],
            "rca_report": rca_report
        }
            
    except Exception as e:
        error_msg = f"RCA Agent error: {str(e)}"
        return {
            "messages": [HumanMessage(content=error_msg)],
            "rca_report": None
        }
