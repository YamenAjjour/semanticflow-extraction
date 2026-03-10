import pandas as pd
import json
import os
from argparse import ArgumentParser
from collections import defaultdict

def evaluate_concepts(predictions, ground_data):
    """
    evaluate the extracted concepts in predictions against ground_data
    :param predictions: a json object containing the elements extracted from the lessons in the ground_truth
    :param ground_data: a data frame containing the elements labeled in the ground_trth
    :return: f1, precision, and recall where a true prediction is considered only if the predicted element matches one of the elements in data ground_data
    """
    stats_by_type = defaultdict(lambda: {'tp': 0, 'fp': 0, 'fn': 0})
    
    # Get all element types from ground truth
    all_element_types = set(ground_data["type"].dropna().astype(str).str.lower())

    # Iterate through predictions
    for module in predictions.get("modules", []):
        for lesson in module.get("lessons", []):
            lesson_id = lesson.get("lesson_id")
            predicted_nodes = lesson.get("nodes", [])
            
            # Filter ground truth for this lesson
            ground_truth_nodes = ground_data[ground_data["lesson_id"] == lesson_id]
            
            # Group ground truth by type
            gt_elements_by_type = defaultdict(set)
            for _, row in ground_truth_nodes.iterrows():
                element = str(row.get("corrected_element", "")).lower()
                el_type = str(row.get("type", "")).lower()
                if element and el_type:
                    gt_elements_by_type[el_type].add(element)
                    all_element_types.add(el_type)
            
            # Group predictions by type
            predicted_elements_by_type = defaultdict(set)
            for node in predicted_nodes:
                text = node.get("text", "").lower()
                el_type = node.get("type", "").lower()
                if text and el_type:
                    predicted_elements_by_type[el_type].add(text)
                    all_element_types.add(el_type)
            
            # Calculate stats per type for this lesson
            for el_type in all_element_types:
                predicted = predicted_elements_by_type[el_type]
                ground_truth = gt_elements_by_type[el_type]
                
                tp = len(predicted.intersection(ground_truth))
                fp = len(predicted - ground_truth)
                fn = len(ground_truth - predicted)
                
                stats_by_type[el_type]['tp'] += tp
                stats_by_type[el_type]['fp'] += fp
                stats_by_type[el_type]['fn'] += fn

    f1_scores = {}
    for el_type, stats in stats_by_type.items():
        tp, fp, fn = stats['tp'], stats['fp'], stats['fn']
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        f1_scores[el_type] = f1
        
    macro_f1 = sum(f1_scores.values()) / len(f1_scores) if f1_scores else 0
    
    return macro_f1, f1_scores

def evaluate_relations(predictions, ground_data):
    """
    evaluate the extracted relations in predictions against ground_data
    :param predictions: a json object containing the relations extracted from the lessons in the ground_truth
    :param ground_data: a data frame containing the relations labeled in the ground_truth
    :return: macro_f1, and a dictionary of f1 scores for each relation type
    """
    stats_by_type = defaultdict(lambda: {'tp': 0, 'fp': 0, 'fn': 0})
    
    # Get all relation types from ground truth
    all_relation_types = set(ground_data["type"].dropna().astype(str).str.lower())

    for module in predictions.get("modules", []):
        for lesson in module.get("lessons", []):
            lesson_id = lesson.get("lesson_id")
            predicted_edges = lesson.get("edges", [])
            nodes = lesson.get("nodes", [])
            node_map = {n["id"]: n["text"] for n in nodes}
            
            ground_truth_relations = ground_data[ground_data["lesson_id"] == lesson_id]
            
            # Group ground truth by type
            gt_relations_by_type = defaultdict(set)
            for _, row in ground_truth_relations.iterrows():
                source = str(row.get("source", "")).lower()
                target = str(row.get("target", "")).lower()
                rel_type = str(row.get("type", "")).lower()
                if source and target and rel_type:
                    gt_relations_by_type[rel_type].add((source, target))
                    all_relation_types.add(rel_type)

            # Group predictions by type
            predicted_relations_by_type = defaultdict(set)
            for edge in predicted_edges:
                rel_type = edge.get("type", "").lower()
                source_id = edge.get("source")
                target_id = edge.get("target")
                source_text = node_map.get(source_id, "").lower()
                target_text = node_map.get(target_id, "").lower()
                
                if source_text and target_text and rel_type:
                    predicted_relations_by_type[rel_type].add((source_text, target_text))
                    all_relation_types.add(rel_type)

            # Calculate stats per type for this lesson
            for rel_type in all_relation_types:
                predicted = predicted_relations_by_type[rel_type]
                ground_truth = gt_relations_by_type[rel_type]
                
                tp = len(predicted.intersection(ground_truth))
                fp = len(predicted - ground_truth)
                fn = len(ground_truth - predicted)
                
                stats_by_type[rel_type]['tp'] += tp
                stats_by_type[rel_type]['fp'] += fp
                stats_by_type[rel_type]['fn'] += fn

    f1_scores = {}
    for rel_type, stats in stats_by_type.items():
        tp, fp, fn = stats['tp'], stats['fp'], stats['fn']
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        f1_scores[rel_type] = f1
        
    macro_f1 = sum(f1_scores.values()) / len(f1_scores) if f1_scores else 0
    
    return macro_f1, f1_scores

def prepare_course_for_annotation(course_data, path_elements_to_annotate, path_relations_to_annotate):
    """
    This function transform the json object in course_data to two  panda data frames. 
    The concept data frames contains the extracted concept, difficulty, the corrected cocnept, and an extra place holder column for the document.
    The prerequisite data frame contains a pair of concepts and the label which should be True as well as an extra place holder column for the document.  
    :param course_data: a json object that contains the modules, lessons, the concepts, and the prerequisites
    :param path_elements_to_annotate: the path for where to save the concepts to annotate
    :param path_preqrequisite_to_annotate: the path of the prerequisite to annotate
    """
    elements_list = []
    relations_list = []

    for module in course_data.get("modules", []):
        for lesson in module.get("lessons", []):
            lesson_id = lesson.get("lesson_id", "")
            
            # Extract concepts
            if "nodes" in lesson:
                for node in lesson["nodes"]:
                    elements_list.append({
                        "lesson_id": lesson_id,
                        "element": node.get("text"),
                        "type": node.get("type"),
                        "difficulty": node.get("difficulty"),
                        "corrected_element": node.get("text"),# Placeholder for annotation
                        "corrected_difficulty": node.get("difficulty"),
                        "lesson_item": "" # Placeholder
                    })
            
            # Extract prerequisites
            if "edges" in lesson and "nodes" in lesson:
                node_map = {n["id"]: n["text"] for n in lesson["nodes"]}
                node_item_map = {n["id"]: n.get("lesson_item_id", "") for n in lesson["nodes"]}
                
                for edge in lesson["edges"]:
                    type = edge.get("type")
                    source_id = edge.get("source")
                    target_id = edge.get("target")
                    source_text = node_map.get(source_id)
                    target_text = node_map.get(target_id)

                    if source_text and target_text:
                        relations_list.append({
                            "lesson_id": lesson_id,
                            "source": source_text,
                            "target": target_text,
                            "type": type,
                            "confidence": edge.get("confidence"),
                            "corrected_type": type,

                        })

    # Create DataFrames
    df_elements = pd.DataFrame(elements_list)
    df_relations = pd.DataFrame(relations_list)
    
    # Ensure directories exist
    os.makedirs(os.path.dirname(path_elements_to_annotate), exist_ok=True)
    os.makedirs(os.path.dirname(path_relations_to_annotate), exist_ok=True)

    # Save to CSV
    df_elements.to_csv(path_elements_to_annotate, index=False)
    df_relations.to_csv(path_relations_to_annotate, index=False)
    
    print(f"Saved elements to {path_elements_to_annotate}")
    print(f"Saved relations to {path_relations_to_annotate}")

def prepare_rationales_for_annotation(course_data, path_element_rationale_to_annotate, path_relation_rationale_to_annotate):
    """
    This function transforms the json object in course_data (with rationales) to two pandas data frames for annotation.
    :param course_data: a json object that contains the modules, lessons, concepts, relations, and rationales
    :param path_element_rationale_to_annotate: path to save element rationales
    :param path_relation_rationale_to_annotate: path to save relation rationales
    """
    element_rationales = []
    relation_rationales = []

    for module in course_data.get("modules", []):
        for lesson in module.get("lessons", []):
            lesson_id = lesson.get("lesson_id", "")
            
            # Element Rationales
            if "nodes" in lesson:
                for node in lesson["nodes"]:
                    if "rationale" in node:
                        element_rationales.append({
                            "lesson_id": lesson_id,
                            "element": node.get("text"),
                            "type": node.get("type"),
                            "rationale": node.get("rationale"),
                            "quality": "" # Placeholder for quality annotation (e.g., 1-5)
                        })
            
            # Relation Rationales
            if "edges" in lesson and "nodes" in lesson:
                node_map = {n["id"]: n["text"] for n in lesson["nodes"]}
                for edge in lesson["edges"]:
                    if "rationale" in edge:
                        source_id = edge.get("source")
                        target_id = edge.get("target")
                        source_text = node_map.get(source_id)
                        target_text = node_map.get(target_id)
                        
                        if source_text and target_text:
                            relation_rationales.append({
                                "lesson_id": lesson_id,
                                "source": source_text,
                                "target": target_text,
                                "type": edge.get("type"),
                                "rationale": edge.get("rationale"),
                                "quality": "" # Placeholder for quality annotation
                            })

    # Create DataFrames
    df_element_rationales = pd.DataFrame(element_rationales)
    df_relation_rationales = pd.DataFrame(relation_rationales)
    
    # Ensure directories exist
    os.makedirs(os.path.dirname(path_element_rationale_to_annotate), exist_ok=True)
    os.makedirs(os.path.dirname(path_relation_rationale_to_annotate), exist_ok=True)

    # Save to CSV
    df_element_rationales.to_csv(path_element_rationale_to_annotate, index=False)
    df_relation_rationales.to_csv(path_relation_rationale_to_annotate, index=False)
    
    print(f"Saved element rationales to {path_element_rationale_to_annotate}")
    print(f"Saved relation rationales to {path_relation_rationale_to_annotate}")

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--create_ground_truth", action="store_true")
    parser.add_argument("--create_rationale_annotation", action="store_true")
    parser.add_argument("--evaluate_elements", action="store_true")
    parser.add_argument("--evaluate_relations", action="store_true")
    parser.add_argument("--predictions", type=str, default="")
    parser.add_argument("--ground_truth", type=str, default="")
    
    args = parser.parse_args()
    
    if args.create_ground_truth:
        sample_json_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data/sample_courses/single_variable_calculus.json")
        if os.path.exists(sample_json_path):
            with open(sample_json_path, 'r') as f:
                course_data = json.load(f)

            output_concepts_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data/evaluation/single_variable_calculus_elements_ground_truth.csv")
            output_prereq_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data/evaluation/single_variable_calculus_relations_ground_truth.csv")

            prepare_course_for_annotation(course_data, output_concepts_path, output_prereq_path)
        else:
            print(f"Sample file not found at {sample_json_path}")
            
    elif args.create_rationale_annotation:
        sample_json_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data/sample_courses/single_variable_calculus_with_rationales.json")
        if os.path.exists(sample_json_path):
            with open(sample_json_path, 'r') as f:
                course_data = json.load(f)
                
            output_el_rat_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data/evaluation/single_variable_calculus_element_rationales.csv")
            output_rel_rat_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data/evaluation/single_variable_calculus_relation_rationales.csv")
            
            prepare_rationales_for_annotation(course_data, output_el_rat_path, output_rel_rat_path)
        else:
            print(f"Sample file not found at {sample_json_path}")

    else:
        if args.evaluate_elements:
            if args.predictions and args.ground_truth:
                with open(args.predictions, 'r') as f:
                    predictions = json.load(f)
                ground_data = pd.read_csv(args.ground_truth)
                macro_f1, f1_by_type = evaluate_concepts(predictions, ground_data)
                print(f"Elements Evaluation - Macro F1: {macro_f1}")
                for el_type, f1 in f1_by_type.items():
                    print(f"  - F1 for '{el_type}': {f1}")
            else:
                print("Please provide --predictions and --ground_truth paths")
        elif args.evaluate_relations:
            if args.predictions and args.ground_truth:
                with open(args.predictions, 'r') as f:
                    predictions = json.load(f)
                ground_data = pd.read_csv(args.ground_truth)
                macro_f1, f1_by_type = evaluate_relations(predictions, ground_data)
                print(f"Relations Evaluation - Macro F1: {macro_f1}")
                for rel_type, f1 in f1_by_type.items():
                    print(f"  - F1 for '{rel_type}': {f1}")
            else:
                print("Please provide --predictions and --ground_truth paths")