
from bs4 import BeautifulSoup
import json
import time
import random
import yaml
import os
import re
from argparse import ArgumentParser
from collections import deque, defaultdict
from playwright.sync_api import sync_playwright, TimeoutError

from llm_client import LLMClient
from rationale import extract_rationales
from utils import topologically_sort_lesson_nodes


def extract_modules(soup):
    """
    Extracts all h3 elements within divs that have data-testid inside a div with the id "modules".
    :param soup: The BeautifulSoup object of the course page.
    :return: A list of BeautifulSoup h3 elements representing the modules.
    """
    modules = []
    modules_container = soup.find("div", id="modules")
    
    if modules_container:
        # Find all divs with a data-testid attribute inside the container
        items_with_testid = modules_container.find_all("div", attrs={"data-testid": True})
        
        for item in items_with_testid:
            h3 = item.find("h3")
            if h3:
                modules.append(h3)
                
    return modules

def clean_title(text):
    """
    Removes unwanted metadata from lesson item titles.
    :param text: The original title text.
    :return: The cleaned title.
    """
    # Remove "Due, [Date], [Time]" pattern
    text = re.sub(r"Due, [A-Za-z]{3} \d{1,2}, \d{1,2}:\d{2} [AP]M [A-Z]{3}", "", text)

    text = text.replace("Graded Assignment", "")
    text = text.replace( "Video Resume . Click to resume", "")
    text = re.sub(r". Duration:\s*\d+\s*minutes\s*\d+\s*min", "", text)
    text = re.sub(r"\d+ min", "", text)
    text = re.sub(r"Grade: --", "", text)

    # Remove bullet points and extra whitespace
    text = text.replace("•", "")
    text = re.sub(r"\s+", " ", text).strip()
    if text.endswith("Video") and len(text) > 5:
        text = text[:-5].strip()
    return text

def clean_content(content):
    """
    Removes zero-width spaces and non-breaking spaces from content.
    :param content: The text content to clean.
    :return: The cleaned text.
    """
    content = content.replace("\u200b", "").replace("\u00a0", " ")
    return content

def extract_page_content(page, url, item_type):
    """
    Visits the item URL and extracts content (transcript for video, text for reading).
    :param page: The Playwright page object.
    :param url: The URL of the item to visit.
    :param item_type: The type of item ('video' or 'reading').
    :return: The extracted content, or an error message if not found.
    """
    print(f"Visiting {item_type}: {url}")
    try:
        page.goto(url, wait_until="networkidle", timeout=420000)
        time.sleep(random.randint(1,5)) # Wait for rendering
        
        if item_type == "video":
            # Attempt to extract transcript
            # Looking for a div that likely contains the transcript
            transcript = page.query_selector("div[class*='rc-Transcript']")
            if transcript:
                text =  transcript.inner_text()
                text = clean_content(text)
                return text

            return "Transcript not found"
            
        elif item_type == "reading":
            # Attempt to extract reading text
            # Looking for a div that likely contains the reading content
            content = page.query_selector("div[class*='rc-ReadingItem']")
            if not content:
                content = page.query_selector("div[class*='CmlItem']")
            if content:
                text = content.inner_text()
                text = clean_content(text)
                return text
            return "Reading content not found"
            
    except TimeoutError:
        print(f"Timeout visiting {url}")
        return None
    except Exception as e:
        print(f"Error visiting {url}: {e}")
        return None
    return None

def extract_lessons(page, url, modules):
    """
    Extracts lessons from each module by navigating to the module page.
    :param page: The Playwright page object.
    :param url: The base URL of the course.
    :param modules: A list of module dictionaries containing module_id and title.
    :return: A tuple containing:
        - processed_modules (list): List of modules with extracted lessons.
        - cross_scale_links (list): List of relationships between lessons and modules.
    """
    processed_modules = []
    cross_scale_links = []


    for i, module_data in enumerate(modules, start=1):
        module_id = module_data["module_id"]
        module_title = module_data["title"]
        
        module_url = f"{url}/home/module/{i}"
        print(f"Processing Module {i}: {module_url}")
        
        module_obj = {
            "module_id": module_id,
            "title": module_title,
            "lessons": []
        }

        try:
            ## The following is a bug that the first lesson is always nto properly loaded
            page.goto(module_url, wait_until="networkidle", timeout=42000)
            page.goto(module_url, wait_until="networkidle", timeout=42000)

            content = page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Find all divs with class rc-ItemGroupLesson
            lesson_groups = soup.find_all("div", class_="rc-ItemGroupLesson")
            if not lesson_groups:
                lesson_groups = soup.find_all("div", class_="rc-ModuleSection")
            if lesson_groups:
                for l_idx, group in enumerate(lesson_groups, start=1):
                    # Find lesson title in nested h2
                    lesson_title_elem = group.find("h2")
                    lesson_title = lesson_title_elem.get_text(strip=True) if lesson_title_elem else f"Lesson {l_idx}"
                    if "1 graded assessment left" in lesson_title:
                        lesson_title = lesson_title.replace("1 graded assessment left", "")
                    lesson_id = f"{module_id}-l{l_idx}"
                    items = []

                    # Find ul within this group
                    ul = group.find("ul")
                    if ul:
                        lis = ul.find_all("li")
                        for li in lis:
                            a = li.find("a")
                            if a:
                                link = a.get("href", "")
                                if link.startswith("/"):
                                    link = f"https://www.coursera.org{link}"
                                text = a.get_text(" ", strip=True)
                                
                                # Determine type before cleaning
                                is_video = "Video" in text
                                is_quiz = "Quiz" in text or "Assignment" in text
                                
                                # Clean the text
                                cleaned_title = clean_title(text)
                                
                                if is_video:
                                   content = extract_page_content(page, link, "video")

                                   items.append((cleaned_title, "video", content))
                                elif is_quiz:
                                   items.append((cleaned_title, "quiz", link))
                                else:
                                    content = extract_page_content(page, link, "reading")
                                    items.append((cleaned_title, "reading", content))

                    module_obj["lessons"].append({
                        "lesson_id": lesson_id,
                        "title": lesson_title,
                        "scale": "lesson",
                        "items": items
                    })
                        
                    cross_scale_links.append({
                        "lesson_node": lesson_id,
                        "module_node": module_id,
                        "relationship": "part_of"
                    })

            else:
                print(f"No lessons found for module {i}")

        except TimeoutError:
            print(f"Timeout processing module {i}")
        except Exception as e:
            print(f"Error processing module {i}: {e}")
            
        processed_modules.append(module_obj)

    return processed_modules, cross_scale_links

def crawl_coursera_course(url, path=None, domain="unknown", cookies=None ):
    """
    Crawls a Coursera course URL to extract modules, lessons, and items.
    :param url: The URL of the course home page.
    :param path: Path to save the output JSON file.
    :param domain: The domain of the course.
    :param cookies: Cookies for authentication.
    :return: The crawled course data.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True) # Set headless=False to see the browser
        context = browser.new_context()

        if cookies:
            if isinstance(cookies, str):
                cookie_list = []
                for item in cookies.split(';'):
                    if '=' in item:
                        name, value = item.strip().split('=', 1)
                        cookie_list.append({'name': name, 'value': value, 'domain': '.coursera.org', 'path': '/'})
                context.add_cookies(cookie_list)
            else: # assume it's a list of dicts
                context.add_cookies(cookies)

        page = context.new_page()
        try:
            page.goto(url, wait_until="networkidle", timeout=30000)
        except TimeoutError:
            print(f"Timeout loading course page: {url}")
            # Continue anyway, maybe content loaded partially
        
        content = page.content()
        soup = BeautifulSoup(content, 'html.parser')
        
        course_title = "Untitled Course"
        if soup.title:
            course_title = soup.title.get_text(strip=True).replace(" | Coursera", "")

        course_id = "course_identifier"
        base_url = url
        if "/learn/" in url:
            parts = url.split("/learn/")
            if len(parts) > 1:
                course_slug = parts[1].split("/")[0]
                course_id = course_slug
                base_url = url.split("/learn/")[0] + "/learn/" + course_slug

        course_data = {
            "course_id": course_id,
            "domain_type": domain,
            "course_title": course_title,
            "modules": [],
            "cross_scale_links": []
        }
        
        modules_h3 = extract_modules(soup)
        print(f"Found {len(modules_h3)} modules.")
        
        initial_modules = []
        for i, module_h3 in enumerate(modules_h3, start=1):
            module_title = module_h3.get_text(strip=True)
            module_id = f"m{i}"
            initial_modules.append({
                "module_id": module_id,
                "title": module_title
            })

        processed_modules, links = extract_lessons(page, base_url, initial_modules)
        
        # Extract content for each item

        course_data["modules"] = processed_modules
        course_data["cross_scale_links"] = links

        browser.close()

        if path:
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(course_data, f, indent=2)
                print(f"Saved output to {path}")
            except Exception as e:
                print(f"Failed to save output: {e}")

        return course_data


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

def extract_semantic_flows(course_data, domain="unknown"):
    """
    Extracts semantic elements and their relationships from the crawled course data.
    :param course_data: The crawled course data.
    :param domain: The domain of the course.
    :return: The course data with extracted semantic flows (nodes and edges).
    """
    client = LLMClient()
    prompts = load_prompts()
    modules_titles = [module["title"] for module in course_data["modules"]]
    relation_mapper = {"assess": "ASSESSES", "prerequisite": "PREREQUISITE_FOR", "elaborate": "ELABORATED_BY", "apply": "APPLIES_TO", "relate": "RELATES_TO"}
    for module in course_data["modules"]:
        node_id_counter = 1
        node_map = {} # Map concept text to node ID
        for lesson in module["lessons"]:
            nodes = []
            edges = []
            assessment_literals = [item[0] for item in lesson["items"] if item[1] == "quiz"]
            lesson_content = []
            for item_idx, item in enumerate(lesson["items"]):
                if item[1] == "reading" or item[1] == "video":
                    content = item[2]
                    item_title = item[0]
                    item_type = item[1]
                    lesson_content.append(f"--- {item_type.upper()}: {item_title} ---\n{content}")
            
            if not lesson_content:
                continue
                
            full_lesson_text = "\n\n".join(lesson_content)
            
            # Extract concepts
            elements_responses = client.prompt(
                "gpt-4o",
                prompts["extract_elements"], 
                {"document": full_lesson_text, "domain": domain, "course": course_data.get("course_title", ""), "modules": modules_titles},
                constraints=prompts["extract_elements"].get("constraints")
            )
            
            elements = elements_responses.get("elements", []) if elements_responses else []
            concept_literals = [e["element"] for e in elements if e.get("element") and e.get("type") == "concept"]
            method_literals = [e["element"] for e in elements if e.get("element") and e.get("type") == "method"]
            explanation_literals = [e["element"] for e in elements if e.get("element") and e.get("type") == "explanation"]
            example_literals = [e["element"] for e in elements if e.get("element") and e.get("type") == "example"]
            # Extract relations
            relations_response = client.prompt(
                "gpt-4o",
                prompts["extract_relations"], 
                {
                    "document": full_lesson_text, "domain": domain, "concepts": ", ".join(concept_literals),
                    "methods": ", ".join(method_literals), "examples": ", ".join(example_literals), "explanations": ", ".join(explanation_literals),
                    "assessments": ", ".join(assessment_literals),
                    "course": course_data.get("course_title", ""), "modules": modules_titles
                },
                constraints=prompts["extract_relations"].get("constraints")
            )
            
            relations = relations_response.get("relations", []) if relations_response else []
            
            # Process concepts into nodes
            for element_obj in elements:
                element_text = element_obj.get("element")
                difficulty = element_obj.get("difficulty")
                type = element_obj.get("type")
                if element_text and element_text not in node_map:
                    node_id = f"n{node_id_counter}"
                    node_id_counter += 1
                    node_map[element_text] = node_id
                    
                    nodes.append({
                        "id": node_id,
                        "text": element_text,
                        "type": type,
                        "difficulty": difficulty,
                        "lesson_id": lesson['lesson_id']
                    })
            
            # Add quizzes as assessment nodes
            for quiz_title in assessment_literals:
                if quiz_title not in node_map:
                    node_id = f"n{node_id_counter}"
                    node_id_counter += 1
                    node_map[quiz_title] = node_id
                    
                    nodes.append({
                        "id": node_id,
                        "text": quiz_title,
                        "type": "assessment",
                        "difficulty": "medium", # Or determine based on quiz type
                        "lesson_id": lesson['lesson_id']
                    })
            
            # Process relations into edges
            for relation in relations:
                source_text = relation.get("source")
                target_text = relation.get("target")
                confidence = relation.get("confidence")
                rel_type = relation.get("type")
                if source_text in node_map and target_text in node_map:
                    source_id = node_map[source_text]
                    target_id = node_map[target_text]
                    
                    edges.append({
                        "source": source_id,
                        "target": target_id,
                        "type": relation_mapper.get(rel_type, rel_type),
                        "confidence": confidence
                    })
            
            # Topologically sort the nodes
            lesson["nodes"] = topologically_sort_lesson_nodes(nodes, edges)
            lesson["edges"] = edges
    
    # Extract rationales
    course_data = extract_rationales(course_data, domain=domain)

    return course_data
if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--url", type=str, required=True)
    parser.add_argument("--domain", type=str)
    parser.add_argument("--data", type=str)

    args = parser.parse_args()
    
    cookies = None
    config_path = "config.yaml"
    if not os.path.exists(config_path):
        parent_config = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.yaml")
        if os.path.exists(parent_config):
            config_path = parent_config
            
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                cookies = config.get('cookies')
                print(f"Loaded cookies from {config_path}")
        except Exception as e:
            print(f"Error reading config file: {e}")
    else:
        print("No config.yaml found.")
    crawled_course_path = args.data.replace(".json", "_crawled.json")
    if not os.path.exists(crawled_course_path):
        course_data = crawl_coursera_course(args.url, crawled_course_path, domain=args.domain or "unknown", cookies=cookies)
    else:
        course_data = json.load(open(crawled_course_path, 'r'))
        
    semantic_flow = extract_semantic_flows(course_data, domain=args.domain or "unknown")
    
    with open(args.data, 'w', encoding='utf-8') as f:
        json.dump(semantic_flow, f, indent=2)
    print(f"Saved semantic flow to {args.data}")
