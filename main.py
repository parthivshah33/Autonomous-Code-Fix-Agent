"""Main entry point for the Multi-Agent Code Fixer System"""
import sys
import argparse
from pathlib import Path
from typing import Optional

from src.graph.workflow import build_workflow, create_initial_state
from src.utils.logger import save_logs, save_final_state, get_logger
from src.config import DATA_INPUT_DIR, DATA_OUTPUT_DIR, TARGET_ROOT_DIR


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(
        description="Multi-Agent Code Fixer System - Analyzes errors and generates fixes"
    )
    parser.add_argument(
        "error_file",
        type=str,
        help="Path to the error/trace JSON file"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=DATA_OUTPUT_DIR,
        help=f"Output directory for logs and fixed files (default: {DATA_OUTPUT_DIR})"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "--target-root",
        type=str,
        default=None,
        help="Root directory of the target codebase being fixed (required if trace.json contains Linux paths)"
    )
    
    args = parser.parse_args()
    
    # Validate input file
    error_file_path = Path(args.error_file)
    if not error_file_path.exists():
        print(f"Error: File not found: {error_file_path}")
        sys.exit(1)
    
    # Resolve absolute path
    error_file_path = error_file_path.resolve()
    
    # Handle target root directory
    target_root_dir = args.target_root or TARGET_ROOT_DIR
    if target_root_dir:
        target_root_path = Path(target_root_dir)
        if not target_root_path.exists():
            print(f"Error: Target root directory not found: {target_root_path}")
            print("Please ensure the target codebase directory exists and is accessible.")
            sys.exit(1)
        target_root_dir = str(target_root_path.resolve())
    
    print("=" * 80)
    print("Multi-Agent Code Fixer System")
    print("=" * 80)
    print(f"Input Error File: {error_file_path}")
    if target_root_dir:
        print(f"Target Root Directory: {target_root_dir}")
    else:
        print("Target Root Directory: Not specified (using paths as-is)")
    print(f"Output Directory: {args.output_dir}")
    print("=" * 80)
    print()
    
    try:
        # Build workflow
        print("Building workflow...")
        graph = build_workflow()
        
        # Create initial state
        print("Initializing state...")
        initial_state = create_initial_state(str(error_file_path), target_root_dir)
        
        # Execute workflow
        print("\n" + "=" * 80)
        print("Starting Agent Pipeline Execution")
        print("=" * 80)
        print("\n[1/3] RCA Agent: Analyzing error...")
        
        # Run the graph
        final_state = graph.invoke(initial_state)
        
        print("\n" + "=" * 80)
        print("Pipeline Execution Complete")
        print("=" * 80)
        
        # Display results
        print("\nResults Summary:")
        print("-" * 80)
        
        if final_state.get("rca_report"):
            rca = final_state["rca_report"]
            print(f"[OK] RCA Report Generated")
            print(f"  - Error Type: {rca.error_type}")
            print(f"  - Severity: {rca.severity}")
            print(f"  - Affected File: {rca.affected_file}")
            print(f"  - Root Cause: {rca.root_cause_summary}")
        else:
            print("[FAIL] RCA Report: Failed")
        
        if final_state.get("fix_plan"):
            plan = final_state["fix_plan"]
            print(f"\n[OK] Fix Plan Generated")
            print(f"  - Summary: {plan.fix_summary}")
            print(f"  - Changes: {len(plan.changes)} code modification(s)")
        else:
            print("\n[FAIL] Fix Plan: Failed")
        
        if final_state.get("patch_result"):
            patch = final_state["patch_result"]
            print(f"\n[OK] Patch Generated")
            print(f"  - Status: {patch.status}")
            print(f"  - Original File: {patch.original_file}")
            print(f"  - Fixed File: {patch.fixed_file}")
            print(f"  - Summary: {patch.applied_changes_summary}")
        else:
            print("\n[FAIL] Patch Result: Failed")
        
        # Save logs and final state
        print("\n" + "=" * 80)
        print("Saving Logs and Final State")
        print("=" * 80)
        
        history_file = save_logs()
        state_file = save_final_state(final_state)
        
        print(f"[OK] Message History: {history_file}")
        print(f"[OK] Final State: {state_file}")
        
        # Save individual outputs if available
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if final_state.get("rca_report"):
            rca_file = output_dir / "rca_report.json"
            with open(rca_file, 'w', encoding='utf-8') as f:
                f.write(final_state["rca_report"].model_dump_json(indent=2))
            print(f"[OK] RCA Report: {rca_file}")
        
        if final_state.get("fix_plan"):
            plan_file = output_dir / "fix_plan.json"
            with open(plan_file, 'w', encoding='utf-8') as f:
                f.write(final_state["fix_plan"].model_dump_json(indent=2))
            print(f"[OK] Fix Plan: {plan_file}")
        
        if final_state.get("patch_result"):
            patch_file = output_dir / "patch_result.json"
            with open(patch_file, 'w', encoding='utf-8') as f:
                f.write(final_state["patch_result"].model_dump_json(indent=2))
            print(f"[OK] Patch Result: {patch_file}")
        
        print("\n" + "=" * 80)
        print("Execution Complete!")
        print("=" * 80)
        
        # Exit with error if any step failed
        if not all([final_state.get("rca_report"), 
                   final_state.get("fix_plan"), 
                   final_state.get("patch_result")]):
            print("\nWarning: Some agents failed. Check logs for details.")
            sys.exit(1)
        
    except Exception as e:
        print(f"\nError during execution: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
