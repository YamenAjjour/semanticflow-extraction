import json
import os
from argparse import ArgumentParser
from llm_client import LLMClient
from utils import topologically_sort_lesson_nodes

def load_prompts():
    """
    Loads prompts from the data/prompts.json file.
    :return: A dictionary containing the loaded prompts.
    """
    prompts_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "prompts.json")
    if os.path.exists(prompts_path):
        with open(prompts_path, 'r') as f:
            return json.load(f)
    return {}

def format_elements_string(nodes, filter_types=None):
    """
    Formats a list of nodes into a string for the LLM prompt.
    :param nodes: A list of node dictionaries.
    :param filter_types: A set of types to include (e.g., {"concept", "method"}). If None, all types are included.
    :return: A formatted string of elements.
    """
    if filter_types:
        return ", ".join([f"{n['text']} ({n['type']})" for n in nodes if n['type'] in filter_types])
    return ", ".join([f"{n['text']} ({n['type']})" for n in nodes])

def format_relations_string(nodes, edges):
    """
    Formats a list of edges into a string for the LLM prompt, in a sorted order.
    :param nodes: A list of node dictionaries (used for sorting).
    :param edges: A list of edge dictionaries.
    :return: A formatted string of relations.
    """
    sorted_nodes = topologically_sort_lesson_nodes(nodes, edges)
    node_map = {n["id"]: n["text"] for n in sorted_nodes}
    
    relations_str_list = []
    for node in sorted_nodes:
        node_id = node['id']
        outgoing_edges = [e for e in edges if e['source'] == node_id]
        for e in outgoing_edges:
            target_text = node_map.get(e['target'])
            if target_text:
                relations_str_list.append(f"{node['text']} -> {target_text} ({e['type']})")
    
    return ", ".join(relations_str_list)

def extract_rationales(course_data, domain="unknown"):
    """
    Extracts rationales for the extracted concepts and relations in the course data.
    
    Args:
        course_data (dict): The course data containing modules, lessons, nodes, and edges.
        domain (str): The domain of the course.
        
    Returns:
        dict: The updated course data with rationales.
    """
    client = LLMClient()
    prompts = load_prompts()
    
    if "extract_elements_rationales" not in prompts:
        print("Warning: 'extract_elements_rationales' prompt not found in prompts.json")
        return course_data
    modules_titles = [module["title"] for module in course_data["modules"]]
    for module in course_data.get("modules", []):
        for lesson in module.get("lessons", []):
            # Gather lesson content
            lesson_content = []
            for item in lesson.get("items", []):
                if item[1] in ["reading", "video"] and item[2]:
                    lesson_content.append(f"--- {item[1].upper()}: {item[0]} ---\n{item[2]}")
            
            if not lesson_content:
                continue
                
            full_lesson_text = "\n\n".join(lesson_content)
            
            # Prepare concepts and relations for the prompt
            nodes = lesson.get("nodes", [])
            edges = lesson.get("edges", [])
            
            if not nodes:
                continue
            
            # For element rationales, we only care about concepts, methods, and assessments
            element_rationale_nodes = [n for n in nodes if n['type'] in {'concept', 'method', 'assessment'}]
            elements_str_for_elements = format_elements_string(element_rationale_nodes)
            relations_str_for_elements = format_relations_string(element_rationale_nodes, edges)
            
            # Call LLM to extract element rationales
            response_elements = client.prompt(
                "gpt-4o",
                prompts["extract_elements_rationales"],
                {
                    "document": full_lesson_text,
                    "domain": domain,
                    "elements": elements_str_for_elements,
                    "relations": relations_str_for_elements,
                    "course": course_data.get("course_title", ""),
                    "modules": modules_titles
                },
                constraints=prompts["extract_elements_rationales"].get("constraints")
            )
            
            if response_elements and "rationales" in response_elements:
                # Map rationales back to nodes based on text
                rationales = response_elements["rationales"]
                
                # Create a lookup for rationales by element text
                rationale_map = {r["element"]: r["rationale"] for r in rationales if "element" in r and "rationale" in r}
                
                # Assign rationales to nodes
                for node in nodes:
                    node_text = node.get("text")
                    if node_text in rationale_map:
                        node["rationale"] = rationale_map[node_text]
            
            # For relation rationales, we use all nodes
            if "extract_relation_rationales" in prompts:
                all_elements_str = format_elements_string(nodes)
                all_relations_str = format_relations_string(nodes, edges)
                
                response_relations = client.prompt(
                    "gpt-4o",
                    prompts["extract_relation_rationales"],
                    {
                        "document": full_lesson_text,
                        "domain": domain,
                        "elements": all_elements_str,
                        "relations": all_relations_str,
                        "course": course_data.get("course_title", ""),
                        "modules": modules_titles
                    },
                    constraints=prompts["extract_relation_rationales"].get("constraints")
                )
                
                if response_relations and "rationales" in response_relations:
                    relation_rationales = response_relations["rationales"]
                    
                    # Create a lookup for relation rationales
                    rel_rationale_map = {}
                    for r in relation_rationales:
                        if "source" in r and "target" in r and "type" in r and "rationale" in r:
                            key = (r["source"], r["target"], r["type"])
                            rel_rationale_map[key] = r["rationale"]
                    
                    # Assign rationales to edges
                    node_map = {n["id"]: n["text"] for n in nodes}
                    for edge in edges:
                        source_text = node_map.get(edge['source'])
                        target_text = node_map.get(edge['target'])
                        edge_type = edge.get('type')
                        
                        if source_text and target_text and edge_type:
                            key = (source_text, target_text, edge_type)
                            if key in rel_rationale_map:
                                edge["rationale"] = rel_rationale_map[key]
                
    return course_data

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--data", type=str, required=True, help="Path to the course json file")
    parser.add_argument("--domain", type=str, default="unknown")
    
    args = parser.parse_args()
    
    if os.path.exists(args.data):
        with open(args.data, 'r') as f:
            course_data = json.load(f)
            
        updated_data = extract_rationales(course_data, domain=args.domain)
        
        output_path = args.data.replace(".json", "_with_rationales.json")
        with open(output_path, 'w') as f:
            json.dump(updated_data, f, indent=2)
        print(f"Saved data with rationales to {output_path}")
    else:
        print(f"File not found: {args.data}")