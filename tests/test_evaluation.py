import unittest
import pandas as pd
import sys
import os

# Add src directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))

from evaluation import evaluate_concepts, evaluate_relations

class TestEvaluation(unittest.TestCase):

    def test_evaluate_concepts(self):
        """
        Tests the evaluate_concepts function with mock data.
        """
        # Mock Predictions
        predictions = {
            "modules": [{
                "lessons": [{
                    "lesson_id": "l1",
                    "nodes": [
                        {"text": "Concept A", "type": "concept"},
                        {"text": "Concept B", "type": "concept"},
                        {"text": "Method X", "type": "method"},
                        {"text": "Concept C", "type": "concept"} # This will be a FP
                    ]
                }]
            }]
        }
        
        # Mock Ground Truth
        ground_truth_data = {
            "lesson_id": ["l1", "l1", "l1", "l1"],
            "corrected_element": ["Concept A", "Concept B", "Concept D", "Method Y"],
            "type": ["concept", "concept", "concept", "method"]
        }
        ground_truth_df = pd.DataFrame(ground_truth_data)

        # --- Manual Calculation ---
        # For type 'concept':
        #   - Predicted: {A, B, C}
        #   - Ground Truth: {A, B, D}
        #   - TP = 2 (A, B)
        #   - FP = 1 (C)
        #   - FN = 1 (D)
        #   - Precision = 2/3, Recall = 2/3, F1 = 2 * ( (2/3)*(2/3) ) / (2/3 + 2/3) = 0.667
        # For type 'method':
        #   - Predicted: {X}
        #   - Ground Truth: {Y}
        #   - TP = 0
        #   - FP = 1 (X)
        #   - FN = 1 (Y)
        #   - F1 = 0
        # Macro F1 = (0.667 + 0) / 2 = 0.333

        macro_f1, f1_by_type = evaluate_concepts(predictions, ground_truth_df)
        
        self.assertAlmostEqual(f1_by_type['concept'], 0.666, places=2)
        self.assertAlmostEqual(f1_by_type['method'], 0.0, places=2)
        self.assertAlmostEqual(macro_f1, 0.333, places=2)

    def test_evaluate_relations(self):
        """
        Tests the evaluate_relations function with mock data.
        """
        # Mock Predictions
        predictions = {
            "modules": [{
                "lessons": [{
                    "lesson_id": "l1",
                    "nodes": [
                        {"id": "n1", "text": "Concept A"},
                        {"id": "n2", "text": "Concept B"},
                        {"id": "n3", "text": "Concept C"},
                        {"id": "n4", "text": "Concept D"},
                        {"id": "n5", "text": "Concept E"}
                    ],
                    "edges": [
                        {"source": "n1", "target": "n2", "type": "prerequisite"}, # TP for prerequisite
                        {"source": "n3", "target": "n4", "type": "prerequisite"}, # FP for prerequisite
                        {"source": "n1", "target": "n3", "type": "relates_to"}    # TP for relates_to
                    ]
                }]
            }]
        }
        
        # Mock Ground Truth
        ground_truth_data = {
            "lesson_id": ["l1", "l1", "l1"],
            "source": ["Concept A", "Concept A", "Concept E"],
            "target": ["Concept B", "Concept C", "Concept D"],
            "type": ["prerequisite", "relates_to", "prerequisite"]
        }
        ground_truth_df = pd.DataFrame(ground_truth_data)

        # --- Manual Calculation ---
        # For type 'prerequisite':
        #   - Predicted: {(A,B), (C,D)}
        #   - Ground Truth: {(A,B), (E,D)}
        #   - TP = 1 (A->B)
        #   - FP = 1 (C->D)
        #   - FN = 1 (E->D)
        #   - Precision = 1/2, Recall = 1/2, F1 = 0.5
        # For type 'relates_to':
        #   - Predicted: {(A,C)}
        #   - Ground Truth: {(A,C)}
        #   - TP = 1
        #   - FP = 0
        #   - FN = 0
        #   - F1 = 1.0
        # Macro F1 = (0.5 + 1.0) / 2 = 0.75

        macro_f1, f1_by_type = evaluate_relations(predictions, ground_truth_df)
        
        self.assertAlmostEqual(f1_by_type['prerequisite'], 0.5, places=2)
        self.assertAlmostEqual(f1_by_type['relates_to'], 1.0, places=2)
        self.assertAlmostEqual(macro_f1, 0.75, places=2)

if __name__ == '__main__':
    unittest.main()