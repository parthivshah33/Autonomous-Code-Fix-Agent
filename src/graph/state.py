"""Shared state schema for the agent graph"""
from typing import TypedDict, Annotated, Optional, Any
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage
from pydantic import BaseModel, Field
from typing import List, Literal
from enum import Enum


# ============================================================================
# Pydantic Models for Structured Outputs
# ============================================================================

class ErrorSeverity(str, Enum):
    """Severity classification for the error."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ConfidenceLevel(str, Enum):
    """Confidence in the RCA conclusion."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class StackFrame(BaseModel):
    """Represents a single frame in the execution stack."""
    file_path: str = Field(..., description="Absolute path to the file")
    function_name: str = Field(..., description="Function or method name")
    line_number: int = Field(..., description="Line number in the file")
    code_snippet: str = Field(..., description="The actual line of code")
    is_internal: bool = Field(..., description="True if this is application code (not library)")


class CodeContext(BaseModel):
    """Detailed context around the buggy code."""
    buggy_line: str = Field(..., description="The exact line that caused the error")
    line_number: int = Field(..., description="Line number of the buggy code")
    surrounding_code: str = Field(
        ...,
        description="5-10 lines of context around the bug (before and after)"
    )
    relevant_variables: Optional[List[str]] = Field(
        default_factory=list,
        description="Variables or attributes involved in the error"
    )


class RelatedFile(BaseModel):
    """Files that may need to be examined or modified."""
    file_path: str = Field(..., description="Path to the related file")
    reason: str = Field(..., description="Why this file is relevant")
    priority: Literal["high", "medium", "low"] = Field(..., description="How critical this file is")


class RCAReport(BaseModel):
    """Comprehensive Root Cause Analysis Report."""
    error_type: str = Field(..., description="The exception class")
    error_message: str = Field(..., description="The exact error message from the exception")
    severity: ErrorSeverity = Field(..., description="Impact severity of this error")
    root_cause_summary: str = Field(..., description="Concise one-sentence explanation of WHY the error occurred")
    root_cause_detailed: str = Field(..., description="Detailed technical analysis")
    contributing_factors: List[str] = Field(default_factory=list, description="Additional factors that enabled this bug")
    affected_file: str = Field(..., description="Absolute path of the file where the error originated")
    affected_function: str = Field(..., description="Name of the function/method containing the bug")
    affected_class: Optional[str] = Field(None, description="Class name if the function is a method")
    line_number: int = Field(..., description="Exact line number where the code failed")
    code_context: CodeContext = Field(..., description="Detailed code context around the error location")
    execution_flow: List[StackFrame] = Field(..., description="Ordered list of internal stack frames")
    evidence: str = Field(..., description="Key evidence proving this diagnosis")
    full_stack_trace: str = Field(..., description="Complete stack trace for reference")
    related_files: List[RelatedFile] = Field(default_factory=list, description="Other files that should be examined")
    involved_imports: List[str] = Field(default_factory=list, description="Relevant imports or modules")
    database_schema_notes: Optional[str] = Field(None, description="If ORM/database related, notes about expected schema")
    confidence: ConfidenceLevel = Field(..., description="Confidence level in this root cause conclusion")
    assumptions: List[str] = Field(default_factory=list, description="Assumptions made during analysis")
    alternative_hypotheses: List[str] = Field(default_factory=list, description="Other possible explanations")
    fix_category: Literal[
        "typo_correction",
        "type_mismatch",
        "missing_validation",
        "logic_error",
        "missing_import",
        "schema_mismatch",
        "other"
    ] = Field(..., description="Category of fix needed")
    fix_complexity: Literal["simple", "moderate", "complex"] = Field(..., description="Expected complexity of the fix")
    recommended_fix_approach: str = Field(..., description="High-level guidance on how to fix (NO CODE)")


class AtomicCodeChange(BaseModel):
    """Granular instructions for a single code modification."""
    file_path: str = Field(..., description="Absolute path to the file")
    function_name: str = Field(..., description="The specific function or class being modified")
    line_number: Optional[int] = Field(None, description="The specific line number if identifiable")
    original_snippet: str = Field(..., description="The buggy code snippet to search for")
    fixed_snippet: str = Field(..., description="The exact code to replace the buggy snippet with")
    explanation: str = Field(..., description="Why this specific change is being made")


class FixPlan(BaseModel):
    """Comprehensive, actionable plan for the Patch Agent."""
    fix_summary: str = Field(..., description="One-sentence executive summary of the fix")
    detailed_reasoning: str = Field(..., description="Deep dive into why this fix resolves the RCA findings")
    changes: List[AtomicCodeChange] = Field(..., description="List of specific code replacements to be made")
    safety_checks: List[str] = Field(..., description="Pre-checks to perform")
    potential_risks: List[str] = Field(..., description="Possible side effects or edge cases")
    verification_steps: List[str] = Field(..., description="Post-fix steps to ensure the error is gone")


class PatchResult(BaseModel):
    """Result of the patching operation."""
    original_file: str = Field(..., description="Path of the file that was analyzed")
    fixed_file: str = Field(..., description="Path of the newly generated fixed file")
    status: str = Field(..., description="Success or Failed")
    applied_changes_summary: str = Field(..., description="Brief description of changes applied")
    verification_status: str = Field(..., description="Confirmation that syntax and logic were preserved")


# ============================================================================
# Graph State (TypedDict)
# ============================================================================

class AgentGraphState(TypedDict):
    """
    The global state object passed between all nodes in the graph.
    """
    # Entry Point: The path to the error log file uploaded/provided by the user
    input_file_path: str
    
    # Target Root Directory: Root directory of the target codebase being fixed
    target_root_dir: Optional[str]

    # Message History: Stores the full conversation trace (User, AI, Tools)
    messages: Annotated[List[BaseMessage], add_messages]

    # Shared Memory Buckets: Dedicated slots for each agent's structured output
    rca_report: Optional[RCAReport]
    fix_plan: Optional[FixPlan]
    patch_result: Optional[PatchResult]
