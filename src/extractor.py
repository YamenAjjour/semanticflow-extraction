
from bs4 import BeautifulSoup
import json
import time
import random
import yaml
import os
import re
from argparse import ArgumentParser
from playwright.sync_api import sync_playwright

def extract_modules(soup):
    """
    Extracts all h3 elements within divs that have data-testid inside a div with the id "modules".
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
    Examples of text to remove:
    - "Due, Mar 15, 11:59 PM CET"
    - "Graded Assignment"
    - "• Duration: 30 minutes"
    - "30 min"
    - "• Grade: --"
    """
    # Remove "Due, [Date], [Time]" pattern
    text = re.sub(r"Due, [A-Za-z]{3} \d{1,2}, \d{1,2}:\d{2} [AP]M [A-Z]{3}", "", text)

    text = text.replace("Graded Assignment", "")

    text = re.sub(r". Duration:\s*\d+\s*minutes\s*\d+\s*min", "", text)
    text = re.sub(r"\d+ min", "", text)
    text = re.sub(r"Grade: --", "", text)
    
    # Remove bullet points and extra whitespace
    text = text.replace("•", "")
    text = re.sub(r"\s+", " ", text).strip()
    if text.endswith("Video") and len(text) > 5:
        text = text[:-5].strip()
    return text

def extract_lessons(page, url, modules):
    """
    Extracts lessons from each module by navigating to the module page.
    
    Args:
        page (playwright.sync_api.Page): The Playwright page object.
        url (str): The base URL of the course.
        modules (list): A list of module dictionaries containing module_id and title.
        
    Returns:
        tuple: A tuple containing:
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
            page.goto(module_url, wait_until="networkidle")
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
                                clean_text = clean_title(text)
                                
                                if is_video:
                                   items.append((clean_text, "video", link))
                                elif is_quiz:
                                   items.append((clean_text, "quiz", link))
                                else:
                                   items.append((clean_text, "reading", link))

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

        except Exception as e:
            print(f"Error processing module {i}: {e}")
            
        processed_modules.append(module_obj)

    return processed_modules, cross_scale_links

def crawl_coursera_course(url, path=None, domain="unknown", cookies=None ):
    """
    Crawls a Coursera course URL to extract modules, lessons, and items.

    Args:
        url (str): The URL of the course home page.
        cookies (dict): Cookies for authentication (required for quizzes/transcripts).
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True) # Set headless=True for background execution
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
        page.goto(url, wait_until="networkidle")
        
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

    crawl_coursera_course(args.url, args.data, domain=args.domain or "unknown", cookies=cookies)