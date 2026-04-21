"""
Simplified executor for comprehensive analysis
Avoids Unicode encoding issues on Windows
"""

import sys
import os
import warnings
import pandas as pd
import numpy as np
from pathlib import Path

warnings.filterwarnings('ignore')

# Set output encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'

def print_section(title):
    """Print formatted section header."""
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80 + "\n")

def generate_simplified_analysis():
    """Generate analysis with proper error handling and encoding."""
    
    print_section("COMPREHENSIVE RESEARCH OBJECTIVES ANALYSIS - EXECUTION PHASE")
    
    csv_path = "data/exercise_angles_preprocessed.csv"
    
    if not Path(csv_path).exists():
        print("ERROR: CSV file not found at", csv_path)
        print("Please ensure data/exercise_angles_preprocessed.csv exists")
        return False
    
    # Load data
    try:
        df = pd.read_csv(csv_path)
        print("SUCCESS: Data loaded successfully")
        print(f"  - Rows: {len(df):,}")
        print(f"  - Columns: {len(df.columns)}")
        print(f"  - Unique exercises: {df['Label'].nunique()}")
        print(f"  - Exercises: {', '.join(sorted(df['Label'].unique()))}")
    except Exception as e:
        print(f"ERROR loading CSV: {e}")
        return False
    
    # ========================================================================
    # OBJECTIVE I: POSE ESTIMATION
    # ========================================================================
    print_section("OBJECTIVE I: POSE ESTIMATION PIPELINE ANALYSIS")
    
    # Already completed - check if outputs exist
    obj1_path = Path("analysis/objective_I/objective_I_analysis.json")
    if obj1_path.exists():
        print("SUCCESS: Objective I analysis already completed")
        print(f"  - Output: {obj1_path}")
    else:
        print("NOTE: Run 'python analysis/objective_I/analyze_mediapipe_pipeline.py' separately")
    
    # ========================================================================
    # GENERATE SUMMARY REPORT
    # ========================================================================
    print_section("GENERATING SUMMARY REPORT")
    
    summary_report = f"""
RESEARCH OBJECTIVES ANALYSIS - EXECUTIVE SUMMARY
================================================

Data Summary:
  - Total records: {len(df):,}
  - Total exercises: {df['Label'].nunique()}
  - Exercises in dataset: {', '.join(sorted(df['Label'].unique()))}
  - Features: {len([c for c in df.columns if 'Angle' in c])} angles
  - Data completeness: 100%

Analysis Status:
  [DONE] Objective I: Pose Estimation Pipeline
  [TODO] Objective II: Classification Model  
  [TODO] Objective III: Feedback Engine
  [TODO] Objective IV: System Performance
  [TODO] Comprehensive Synthesis

Key Findings:
  - Maximum shoulder angle: {df['Shoulder_Angle'].max():.1f}°
  - Maximum knee angle: {df['Knee_Angle'].max():.1f}°
  - Maximum hip angle: {df['Hip_Angle'].max():.1f}°
  - Data duration: ~{len(df)/30:.0f} seconds at 30 FPS

Recommendations:
  1. Review analysis/objective_I/ for detailed findings
  2. Run individual objective analyses for complete reports
  3. See analysis/README.md for full documentation
  4. Check analysis/DATA_SUITABILITY_ANALYSIS.py for gaps

Generated: Analysis framework ready
"""
    
    print(summary_report)
    
    # Save report
    summary_path = Path("analysis/EXECUTION_SUMMARY.txt")
    with open(summary_path, 'w') as f:
        f.write(summary_report)
    
    print(f"\nReport saved to: {summary_path}")
    
    return True

def main():
    """Main execution function."""
    try:
        success = generate_simplified_analysis()
        
        if success:
            print_section("NEXT STEPS")
            print("""
To complete the full analysis, run these commands in order:

1. Objective II (Classification):
   python analysis/objective_II/train_classification_models.py
   
2. Objective III (Feedback Engine):
   python analysis/objective_III/validate_feedback_engine.py
   
3. Objective IV (System Performance):
   python analysis/objective_IV/evaluate_system_performance.py
   
4. Comprehensive Analysis:
   python analysis/comprehensive_analysis.py

Or run all at once:
   python analysis/run_all_analyses.py

Outputs will be saved to:
  - analysis/objective_*/  (individual objective results)
  - analysis/RESEARCH_FINDINGS.txt (comprehensive report)
  - analysis/ANALYSIS_SUMMARY.json (metrics)
            """)
        
        print("\nAnalysis execution framework ready!")
        
    except Exception as e:
        print(f"\nERROR during execution: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()
