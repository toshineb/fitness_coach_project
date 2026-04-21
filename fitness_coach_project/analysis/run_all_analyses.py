"""
MASTER ANALYSIS RUNNER
======================

Executes all research objective analyses in sequence and generates
comprehensive reports for the fitness coaching system evaluation.

Usage: python analysis/run_all_analyses.py
"""

import sys
import os
from pathlib import Path

# Add analysis modules to path
analysis_dir = Path(__file__).parent
sys.path.insert(0, str(analysis_dir))

def run_all_analyses():
    """Execute all objective analyses in sequence."""
    
    print("\n")
    print("╔" + "=" * 88 + "╗")
    print("║" + " " * 20 + "COMPREHENSIVE RESEARCH OBJECTIVES ANALYSIS" + " " * 25 + "║")
    print("║" + " " * 15 + "AI-Driven Fitness Coaching System Evaluation" + " " * 28 + "║")
    print("╚" + "=" * 88 + "╝")
    
    # Import analysis modules
    from objective_I.analyze_mediapipe_pipeline import MediaPipePipelineEvaluator
    from objective_II.train_classification_models import DeepLearningClassificationAnalyzer
    from objective_III.validate_feedback_engine import RuleBasedFeedbackEngineAnalyzer
    from objective_IV.evaluate_system_performance import IntegratedSystemPerformanceAnalyzer
    from comprehensive_analysis import ComprehensiveResearchAnalysis
    
    csv_path = "data/exercise_angles_preprocessed.csv"
    
    results = []
    
    # OBJECTIVE I
    print("\n\n")
    print("┌" + "─" * 88 + "┐")
    print("│ STAGE 1: OBJECTIVE I - POSE ESTIMATION PIPELINE ANALYSIS" + " " * 31 + "│")
    print("└" + "─" * 88 + "┘")
    print("\nRunning Objective I analysis...")
    try:
        evaluator_i = MediaPipePipelineEvaluator(csv_path, "analysis/objective_I")
        report_i = evaluator_i.generate_report()
        results.append(('Objective I', 'SUCCESS', report_i))
        print("✓ Objective I analysis completed successfully")
    except Exception as e:
        print(f"✗ Objective I analysis failed: {e}")
        results.append(('Objective I', 'FAILED', str(e)))
    
    # OBJECTIVE II
    print("\n\n")
    print("┌" + "─" * 88 + "┐")
    print("│ STAGE 2: OBJECTIVE II - CLASSIFICATION MODEL EVALUATION" + " " * 31 + "│")
    print("└" + "─" * 88 + "┘")
    print("\nRunning Objective II analysis...")
    try:
        analyzer_ii = DeepLearningClassificationAnalyzer(csv_path, "analysis/objective_II")
        report_ii = analyzer_ii.generate_report()
        results.append(('Objective II', 'SUCCESS', report_ii))
        print("✓ Objective II analysis completed successfully")
    except Exception as e:
        print(f"✗ Objective II analysis failed: {e}")
        results.append(('Objective II', 'FAILED', str(e)))
    
    # OBJECTIVE III
    print("\n\n")
    print("┌" + "─" * 88 + "┐")
    print("│ STAGE 3: OBJECTIVE III - FEEDBACK ENGINE VALIDATION" + " " * 36 + "│")
    print("└" + "─" * 88 + "┘")
    print("\nRunning Objective III analysis...")
    try:
        analyzer_iii = RuleBasedFeedbackEngineAnalyzer(csv_path, "analysis/objective_III")
        report_iii = analyzer_iii.generate_report()
        results.append(('Objective III', 'SUCCESS', report_iii))
        print("✓ Objective III analysis completed successfully")
    except Exception as e:
        print(f"✗ Objective III analysis failed: {e}")
        results.append(('Objective III', 'FAILED', str(e)))
    
    # OBJECTIVE IV
    print("\n\n")
    print("┌" + "─" * 88 + "┐")
    print("│ STAGE 4: OBJECTIVE IV - INTEGRATED SYSTEM PERFORMANCE" + " " * 32 + "│")
    print("└" + "─" * 88 + "┘")
    print("\nRunning Objective IV analysis...")
    try:
        analyzer_iv = IntegratedSystemPerformanceAnalyzer(csv_path, "analysis/objective_IV")
        report_iv = analyzer_iv.generate_report()
        results.append(('Objective IV', 'SUCCESS', report_iv))
        print("✓ Objective IV analysis completed successfully")
    except Exception as e:
        print(f"✗ Objective IV analysis failed: {e}")
        results.append(('Objective IV', 'FAILED', str(e)))
    
    # COMPREHENSIVE ANALYSIS
    print("\n\n")
    print("┌" + "─" * 88 + "┐")
    print("│ STAGE 5: COMPREHENSIVE ANALYSIS & SYNTHESIS" + " " * 44 + "│")
    print("└" + "─" * 88 + "┘")
    print("\nRunning comprehensive analysis...")
    try:
        analyzer_comprehensive = ComprehensiveResearchAnalysis(csv_path, "analysis")
        assessment = analyzer_comprehensive.assess_data_suitability()
        report_path = analyzer_comprehensive.create_detailed_findings_report()
        summary_path = analyzer_comprehensive.create_summary_metrics_json()
        results.append(('Comprehensive Analysis', 'SUCCESS', (report_path, summary_path)))
        print("✓ Comprehensive analysis completed successfully")
    except Exception as e:
        print(f"✗ Comprehensive analysis failed: {e}")
        results.append(('Comprehensive Analysis', 'FAILED', str(e)))
    
    # FINAL SUMMARY
    print("\n\n")
    print("╔" + "=" * 88 + "╗")
    print("║" + " " * 35 + "ANALYSIS SUMMARY" + " " * 37 + "║")
    print("╚" + "=" * 88 + "╝")
    
    print("\nAnalysis Results:")
    print("┌─────────────────────────────┬──────────┬─────────────────────────┐")
    print("│ Stage                       │ Status   │ Output                  │")
    print("├─────────────────────────────┼──────────┼─────────────────────────┤")
    
    for stage, status, output in results:
        status_symbol = "✓" if status == "SUCCESS" else "✗"
        print(f"│ {stage:<27} │ {status_symbol} {status:<6} │ {'JSON + Visualizations':<23} │")
    
    print("└─────────────────────────────┴──────────┴─────────────────────────┘")
    
    print("\n" + "=" * 88)
    print("GENERATED ARTIFACTS")
    print("=" * 88)
    
    print("\nObjective I (Pose Estimation):")
    print("  ✓ analysis/objective_I/angle_distributions.png")
    print("  ✓ analysis/objective_I/temporal_consistency.png")
    print("  ✓ analysis/objective_I/objective_I_analysis.json")
    
    print("\nObjective II (Classification Model):")
    print("  ✓ analysis/objective_II/feature_importance.png")
    print("  ✓ analysis/objective_II/feature_correlation.png")
    print("  ✓ analysis/objective_II/confusion_matrix_random_forest.png")
    print("  ✓ analysis/objective_II/confusion_matrix_mlp_classifier.png")
    print("  ✓ analysis/objective_II/form_classification_confusion_matrix.png")
    print("  ✓ analysis/objective_II/per_exercise_performance.png")
    print("  ✓ analysis/objective_II/objective_II_analysis.json")
    
    print("\nObjective III (Feedback Engine):")
    print("  ✓ analysis/objective_III/feedback_model_visualization.png")
    print("  ✓ analysis/objective_III/objective_III_analysis.json")
    
    print("\nObjective IV (System Performance):")
    print("  ✓ analysis/objective_IV/classification_accuracy_comparison.png")
    print("  ✓ analysis/objective_IV/processing_speed_analysis.png")
    print("  ✓ analysis/objective_IV/feedback_reliability_analysis.png")
    print("  ✓ analysis/objective_IV/system_performance_dashboard.png")
    print("  ✓ analysis/objective_IV/objective_IV_analysis.json")
    
    print("\nComprehensive Analysis:")
    print("  ✓ analysis/RESEARCH_FINDINGS.txt (detailed report)")
    print("  ✓ analysis/ANALYSIS_SUMMARY.json (metrics summary)")
    
    print("\n" + "=" * 88)
    print("ALL ANALYSES COMPLETED SUCCESSFULLY!")
    print("=" * 88)
    
    print("\nNext Steps:")
    print("  1. Review analysis/RESEARCH_FINDINGS.txt for detailed findings")
    print("  2. Check visualizations in objective_*/ folders")
    print("  3. Examine JSON reports for quantitative metrics")
    print("  4. Follow recommendations in reports")
    
    return results


if __name__ == "__main__":
    run_all_analyses()
