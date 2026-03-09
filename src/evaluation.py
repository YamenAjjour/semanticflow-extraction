import pandas as pd
import json
import os

def prepare_course_for_annotation(course_data, path_concepts_to_annotate, path_prerequisite_to_annotate):
    """
    This function transform the json object in course_data to two  panda data frames. 
    The concept data frames contains the extracted concept, difficulty, the corrected cocnept, and an extra place holder column for the document.
    The prerequisite data frame contains a pair of concepts and the label which should be True as well as an extra place holder column for the document.  
    :param course_data: a json object that contains the modules, lessons, the concepts, and the prerequisites
    :param path_concepts_to_annotate: the path for where to save the concepts to annotate
    :param path_preqrequisite_to_annotate: the path of the prerequisite to annotate
    """
    concepts_list = []
    prerequisites_list = []

    for module in course_data.get("modules", []):
        for lesson in module.get("lessons", []):
            lesson_id = lesson.get("lesson_id", "")
            
            # Extract concepts
            if "nodes" in lesson:
                for node in lesson["nodes"]:
                    concepts_list.append({
                        "lesson_id": lesson_id,
                        "lesson_item_id": node.get("lesson_item_id", ""),
                        "concept": node.get("text"),
                        "difficulty": node.get("difficulty"),
                        "corrected_concept": "", # Placeholder for annotation
                        "lesson_item": "" # Placeholder
                    })
            
            # Extract prerequisites
            if "edges" in lesson and "nodes" in lesson:
                node_map = {n["id"]: n["text"] for n in lesson["nodes"]}
                node_item_map = {n["id"]: n.get("lesson_item_id", "") for n in lesson["nodes"]}
                
                for edge in lesson["edges"]:
                    if edge.get("type") == "PREREQUISITE_FOR":
                        source_id = edge.get("source")
                        target_id = edge.get("target")
                        source_text = node_map.get(source_id)
                        target_text = node_map.get(target_id)
                        
                        if source_text and target_text:
                            prerequisites_list.append({
                                "lesson_id": lesson_id,
                                "source_item_id": node_item_map.get(source_id, ""),
                                "target_item_id": node_item_map.get(target_id, ""),
                                "source": source_text,
                                "target": target_text,
                                "label": True,
                                "source_lesson_item": "", # Placeholder
                                "target_lesson_item": ""
                            })

    # Create DataFrames
    df_concepts = pd.DataFrame(concepts_list)
    df_prerequisites = pd.DataFrame(prerequisites_list)
    
    # Ensure directories exist
    os.makedirs(os.path.dirname(path_concepts_to_annotate), exist_ok=True)
    os.makedirs(os.path.dirname(path_prerequisite_to_annotate), exist_ok=True)

    # Save to CSV
    df_concepts.to_csv(path_concepts_to_annotate, index=False)
    df_prerequisites.to_csv(path_prerequisite_to_annotate, index=False)
    
    print(f"Saved concepts to {path_concepts_to_annotate}")
    print(f"Saved prerequisites to {path_prerequisite_to_annotate}")

if __name__ == "__main__":
    # Example usage
    sample_json_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data/sample_courses/calculus_sample.json")
    
    if os.path.exists(sample_json_path):
        with open(sample_json_path, 'r') as f:
            course_data = json.load(f)
            
        output_concepts_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data/evaluation/calculus_sample_concepts.csv")
        output_prereq_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data/evaluation/calculus_sample_prerequisite.csv")
        
        prepare_course_for_annotation(course_data, output_concepts_path, output_prereq_path)
    else:
        print(f"Sample file not found at {sample_json_path}")