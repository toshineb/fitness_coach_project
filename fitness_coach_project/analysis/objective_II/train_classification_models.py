"""
OBJECTIVE II ANALYSIS: Deep Learning Classification Model
=========================================================

Objective: To design and train a deep learning classification model that recognises 
exercise type and distinguishes between correct and incorrect form by analysing joint 
angle features extracted from publicly available fitness datasets.

This analysis evaluates:
1. Exercise type classification accuracy
2. Form classification (synthetic labels for correct/incorrect)
3. Feature importance and interpretability
4. Model comparison (Random Forest, MLP, Logistic Regression)
5. Generalization performance
6. Feature quality assessment
"""

import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from pathlib import Path
from typing import Dict
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.metrics import (
    accuracy_score, balanced_accuracy_score, confusion_matrix, 
    classification_report, f1_score, roc_auc_score
)
from sklearn.impute import SimpleImputer
import warnings
warnings.filterwarnings('ignore')

class DeepLearningClassificationAnalyzer:
    """Analyzes deep learning classification performance for exercise type and form."""
    
    def __init__(self, csv_path: str, output_dir: str):
        self.csv_path = csv_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.df = pd.read_csv(csv_path)
        
        self.feature_columns = [
            "Shoulder_Angle", "Elbow_Angle", "Hip_Angle", 
            "Knee_Angle", "Ankle_Angle",
            "Shoulder_Ground_Angle", "Elbow_Ground_Angle", 
            "Hip_Ground_Angle", "Knee_Ground_Angle", "Ankle_Ground_Angle"
        ]
        
        self.random_state = 42
        
    def create_form_labels(self) -> pd.DataFrame:
        """
        Create synthetic correct/incorrect form labels based on angle statistics.
        
        Strategy: For each exercise, compute angle distributions.
        Frames within ±1 std of mean are labeled 'Correct'
        Frames outside ±1.5 std are labeled 'Incorrect'
        """
        print("\n" + "=" * 80)
        print("1. FORM LABEL CREATION (SYNTHETIC)")
        print("=" * 80)
        
        df_with_form = self.df.copy()
        form_labels = []
        
        for exercise in df_with_form['Label'].unique():
            exercise_mask = df_with_form['Label'] == exercise
            exercise_data = df_with_form[exercise_mask]
            exercise_indices = exercise_data.index.tolist()
            
            # Calculate Z-scores for all angle features
            angle_data = exercise_data[self.feature_columns].fillna(0).values
            z_scores = np.abs(stats.zscore(angle_data, axis=0))
            
            # Assign form labels based on deviation from exercise-specific norms
            for i, idx in enumerate(exercise_indices):
                z_score_mean = z_scores[i].mean()
                
                if z_score_mean < 1.0:
                    form_labels.append('Correct')
                elif z_score_mean < 1.5:
                    form_labels.append('Near_Form')
                else:
                    form_labels.append('Incorrect')
        
        df_with_form['Form'] = form_labels
        
        form_distribution = df_with_form['Form'].value_counts()
        print(f"\n✓ Form labels created using statistical deviation from exercise norms:")
        print(f"\n  Distribution:")
        for form, count in form_distribution.items():
            pct = (count / len(df_with_form)) * 100
            print(f"    - {form}: {count:,} samples ({pct:.1f}%)")
        
        return df_with_form
    
    def analyze_feature_importance(self, df_with_form: pd.DataFrame) -> Dict:
        """Analyze which features are most important for exercise classification."""
        print("\n" + "=" * 80)
        print("2. FEATURE IMPORTANCE ANALYSIS")
        print("=" * 80)
        
        X = df_with_form[self.feature_columns].fillna(0)
        y = df_with_form['Label']
        
        # Train random forest to get feature importance
        rf = RandomForestClassifier(n_estimators=100, random_state=self.random_state, n_jobs=-1)
        rf.fit(X, y)
        
        # Extract importance scores
        feature_importance = pd.DataFrame({
            'feature': self.feature_columns,
            'importance': rf.feature_importances_
        }).sort_values('importance', ascending=False)
        
        # Visualize
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.barh(feature_importance['feature'], feature_importance['importance'], color='steelblue')
        ax.set_xlabel('Importance Score')
        ax.set_title('Feature Importance for Exercise Type Classification')
        ax.invert_yaxis()
        plt.tight_layout()
        plt.savefig(self.output_dir / 'feature_importance.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print("\n✓ Feature importance ranking (for exercise classification):")
        for idx, row in feature_importance.iterrows():
            print(f"  {row['feature']:30s}: {row['importance']:.4f}")
        
        # Correlation analysis
        correlation_matrix = df_with_form[self.feature_columns].corr()
        
        fig, ax = plt.subplots(figsize=(12, 10))
        sns.heatmap(correlation_matrix, annot=True, fmt='.2f', cmap='coolwarm', 
                   center=0, square=True, ax=ax, cbar_kws={'label': 'Correlation'})
        ax.set_title('Feature Correlation Matrix')
        plt.tight_layout()
        plt.savefig(self.output_dir / 'feature_correlation.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"\n✓ Feature correlation analysis saved")
        
        return {
            'feature_importance': feature_importance.to_dict('list'),
            'top_5_features': feature_importance.head(5)['feature'].tolist()
        }
    
    def train_exercise_classifier(self, df_with_form: pd.DataFrame) -> Dict:
        """Train and evaluate exercise type classifier."""
        print("\n" + "=" * 80)
        print("3. EXERCISE TYPE CLASSIFICATION")
        print("=" * 80)
        
        X = df_with_form[self.feature_columns].fillna(0)
        y = df_with_form['Label']
        
        # Impute missing values
        imputer = SimpleImputer(strategy='median')
        X = pd.DataFrame(imputer.fit_transform(X), columns=self.feature_columns)
        
        # Stratified K-Fold cross-validation
        skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=self.random_state)
        
        models = {
            'Random Forest': RandomForestClassifier(n_estimators=300, max_depth=15, 
                                                   random_state=self.random_state, n_jobs=-1),
            'MLP Classifier': MLPClassifier(hidden_layer_sizes=(128, 64), 
                                           activation='relu', max_iter=500,
                                           random_state=self.random_state)
        }
        
        results = {}
        
        for model_name, model in models.items():
            print(f"\n  Training {model_name}...")
            
            # Cross-validation
            cv_scores = cross_val_score(model, X, y, cv=skf, scoring='accuracy', n_jobs=-1)
            
            # Train on full data for metrics
            model.fit(X, y)
            y_pred = model.predict(X)
            
            # Metrics
            accuracy = accuracy_score(y, y_pred)
            balanced_acc = balanced_accuracy_score(y, y_pred)
            macro_f1 = f1_score(y, y_pred, average='macro', zero_division=0)
            
            results[model_name] = {
                'cv_mean': float(cv_scores.mean()),
                'cv_std': float(cv_scores.std()),
                'cv_scores': cv_scores.tolist(),
                'train_accuracy': float(accuracy),
                'balanced_accuracy': float(balanced_acc),
                'macro_f1': float(macro_f1),
                'classification_report': classification_report(y, y_pred, output_dict=True, zero_division=0)
            }
            
            print(f"    ✓ CV Accuracy: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
            print(f"    ✓ Train Accuracy: {accuracy:.4f}")
            print(f"    ✓ Balanced Accuracy: {balanced_acc:.4f}")
            print(f"    ✓ Macro F1: {macro_f1:.4f}")
            
            # Confusion matrix
            cm = confusion_matrix(y, y_pred, labels=sorted(y.unique()))
            
            fig, ax = plt.subplots(figsize=(12, 10))
            sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax,
                       xticklabels=sorted(y.unique()),
                       yticklabels=sorted(y.unique()))
            ax.set_xlabel('Predicted')
            ax.set_ylabel('True')
            ax.set_title(f'{model_name} - Exercise Classification Confusion Matrix')
            plt.tight_layout()
            plt.savefig(self.output_dir / f'confusion_matrix_{model_name.replace(" ", "_").lower()}.png', 
                       dpi=300, bbox_inches='tight')
            plt.close()
        
        return results
    
    def train_form_classifier(self, df_with_form: pd.DataFrame) -> Dict:
        """Train and evaluate form classification model (Correct vs Incorrect)."""
        print("\n" + "=" * 80)
        print("4. FORM CLASSIFICATION (CORRECT vs INCORRECT)")
        print("=" * 80)
        
        X = df_with_form[self.feature_columns].fillna(0)
        
        # Binary classification: Correct vs Incorrect (excluding Near_Form)
        df_binary = df_with_form[df_with_form['Form'].isin(['Correct', 'Incorrect'])].copy()
        X_binary = df_binary[self.feature_columns].fillna(0)
        y_binary = (df_binary['Form'] == 'Correct').astype(int)
        
        imputer = SimpleImputer(strategy='median')
        X_binary = pd.DataFrame(imputer.fit_transform(X_binary), columns=self.feature_columns)
        
        print(f"\n  Binary classification on {len(df_binary)} samples:")
        print(f"    - Correct form: {(y_binary == 1).sum()}")
        print(f"    - Incorrect form: {(y_binary == 0).sum()}")
        
        # Cross-validation
        skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=self.random_state)
        
        model = RandomForestClassifier(n_estimators=300, max_depth=15, 
                                      random_state=self.random_state, n_jobs=-1)
        
        cv_scores = cross_val_score(model, X_binary, y_binary, cv=skf, scoring='f1')
        
        model.fit(X_binary, y_binary)
        y_pred = model.predict(X_binary)
        
        accuracy = accuracy_score(y_binary, y_pred)
        macro_f1 = f1_score(y_binary, y_pred, average='macro', zero_division=0)
        
        results = {
            'cv_mean_f1': float(cv_scores.mean()),
            'cv_std_f1': float(cv_scores.std()),
            'cv_scores': cv_scores.tolist(),
            'accuracy': float(accuracy),
            'macro_f1': float(macro_f1),
            'classification_report': classification_report(y_binary, y_pred, 
                                                          target_names=['Incorrect', 'Correct'],
                                                          output_dict=True, zero_division=0)
        }
        
        print(f"\n  ✓ CV F1 Score: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
        print(f"  ✓ Accuracy: {accuracy:.4f}")
        print(f"  ✓ Macro F1: {macro_f1:.4f}")
        
        # Confusion matrix
        cm = confusion_matrix(y_binary, y_pred)
        
        fig, ax = plt.subplots(figsize=(8, 6))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Greens', ax=ax,
                   xticklabels=['Incorrect', 'Correct'],
                   yticklabels=['Incorrect', 'Correct'])
        ax.set_xlabel('Predicted')
        ax.set_ylabel('True')
        ax.set_title('Form Classification Confusion Matrix (Correct vs Incorrect)')
        plt.tight_layout()
        plt.savefig(self.output_dir / 'form_classification_confusion_matrix.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        return results
    
    def analyze_model_generalization(self, df_with_form: pd.DataFrame) -> Dict:
        """Analyze model generalization across different exercises."""
        print("\n" + "=" * 80)
        print("5. GENERALIZATION & PER-EXERCISE PERFORMANCE")
        print("=" * 80)
        
        X = df_with_form[self.feature_columns].fillna(0)
        y = df_with_form['Label']
        
        imputer = SimpleImputer(strategy='median')
        X = pd.DataFrame(imputer.fit_transform(X), columns=self.feature_columns)
        
        model = RandomForestClassifier(n_estimators=300, max_depth=15,
                                      random_state=self.random_state, n_jobs=-1)
        
        per_exercise_performance = {}
        
        for exercise in y.unique():
            # Leave-one-exercise-out evaluation
            train_mask = y != exercise
            test_mask = y == exercise
            
            X_train, X_test = X[train_mask], X[test_mask]
            y_train, y_test = y[train_mask], y[test_mask]
            
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            
            acc = accuracy_score(y_test, y_pred)
            f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)
            
            per_exercise_performance[exercise] = {
                'accuracy': float(acc),
                'f1': float(f1),
                'samples': int(len(y_test))
            }
            
            print(f"\n  {exercise}:")
            print(f"    - Leave-one-out accuracy: {acc:.4f}")
            print(f"    - Weighted F1: {f1:.4f}")
            print(f"    - Samples: {len(y_test)}")
        
        # Visualize per-exercise performance
        exercises = list(per_exercise_performance.keys())
        accuracies = [per_exercise_performance[ex]['accuracy'] for ex in exercises]
        
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.bar(range(len(exercises)), accuracies, color='steelblue')
        ax.set_xticks(range(len(exercises)))
        ax.set_xticklabels(exercises, rotation=45, ha='right')
        ax.set_ylabel('Leave-One-Out Accuracy')
        ax.set_title('Model Accuracy by Exercise Type')
        ax.axhline(np.mean(accuracies), color='red', linestyle='--', label=f'Mean: {np.mean(accuracies):.4f}')
        ax.legend()
        ax.grid(alpha=0.3, axis='y')
        plt.tight_layout()
        plt.savefig(self.output_dir / 'per_exercise_performance.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        return per_exercise_performance
    
    def generate_report(self) -> Dict:
        """Generate comprehensive Objective II analysis report."""
        
        print("\n\n")
        print("=" * 80)
        print("OBJECTIVE II: DEEP LEARNING CLASSIFICATION MODEL EVALUATION")
        print("=" * 80)
        
        # Create form labels
        df_with_form = self.create_form_labels()
        
        # Run analyses
        feature_importance = self.analyze_feature_importance(df_with_form)
        exercise_classification = self.train_exercise_classifier(df_with_form)
        form_classification = self.train_form_classifier(df_with_form)
        generalization = self.analyze_model_generalization(df_with_form)
        
        # Compile report
        full_report = {
            'objective': 'II: Deep Learning Classification Model',
            'timestamp': pd.Timestamp.now().isoformat(),
            'data_summary': {
                'total_samples': len(df_with_form),
                'total_exercises': df_with_form['Label'].nunique(),
                'total_features': len(self.feature_columns),
                'form_distribution': df_with_form['Form'].value_counts().to_dict()
            },
            'feature_analysis': feature_importance,
            'exercise_type_classification': exercise_classification,
            'form_classification_results': form_classification,
            'generalization_performance': generalization,
            'limitations': {
                'form_labels_synthetic': True,
                'reason': 'No correct/incorrect labels in original dataset',
                'methodology': 'Created using statistical deviation from exercise-specific norms',
                'validation_needed': 'Requires human annotation to validate synthetic labels'
            }
        }
        
        # Save report
        report_path = self.output_dir / 'objective_II_analysis.json'
        with open(report_path, 'w') as f:
            json.dump(full_report, f, indent=2, default=str)
        
        print(f"\n✓ Full analysis saved to: {report_path}")
        
        return full_report


def main():
    csv_path = "data/exercise_angles_preprocessed.csv"
    output_dir = "analysis/objective_II"
    
    analyzer = DeepLearningClassificationAnalyzer(csv_path, output_dir)
    report = analyzer.generate_report()
    
    print("\n" + "=" * 80)
    print("OBJECTIVE II ANALYSIS COMPLETE")
    print("=" * 80)
    print(f"\nGenerated artifacts in: {output_dir}/")
    print("  - feature_importance.png")
    print("  - feature_correlation.png")
    print("  - confusion_matrix_random_forest.png")
    print("  - confusion_matrix_mlp_classifier.png")
    print("  - form_classification_confusion_matrix.png")
    print("  - per_exercise_performance.png")
    print("  - objective_II_analysis.json")


if __name__ == "__main__":
    main()
