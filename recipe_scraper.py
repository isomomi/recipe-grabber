import requests
import json
from bs4 import BeautifulSoup
import re
import html
from fractions import Fraction

def get_recipe_data(url):
    # user agent (avoid scraper blocks)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:145.0) Gecko/20100101 Firefox/145.0'
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()  # for 404s/500s

    soup = BeautifulSoup(response.content, 'html.parser')

    # Find ALL JSON-LD script tags
    # Websites often have multiple data blocks (Breadcrumbs, Organization, Recipe)
    script_tags = soup.find_all('script', {'type': 'application/ld+json'})

    if not script_tags:
        return "No JSON-LD data found."

    target_recipe = None

    # 3. Loop through them to find the one that is a 'Recipe'
    for script in script_tags:
        try:
            # The content inside the tag is just a string, so we parse it to a dict
            data = json.loads(script.string)

            # Standardize to a list of items to search through
            search_items = []
            if isinstance(data, list):
                search_items = data
            elif isinstance(data, dict):
                if '@graph' in data:
                    search_items = data['@graph']
                else:
                    search_items = [data]

            for item in search_items:
                # Check @type safely
                type_val = item.get('@type')
                
                # Handle case where @type is a string (e.g., "Recipe")
                if isinstance(type_val, str):
                    if type_val == 'Recipe':
                        target_recipe = item
                        break
                # Handle case where @type is a list (e.g., ["Recipe", "NewsArticle"])
                elif isinstance(type_val, list):
                    if 'Recipe' in type_val:
                        target_recipe = item
                        break

            if target_recipe:
                break

        except json.JSONDecodeError:
            continue

    if target_recipe:
        return target_recipe
    else:
        return "No recipe schema found on this page."

def format_ingredient(text): # converts decimals to fractions, e.g. 0.6666... -> 2/3
    text = html.unescape(text) # fix formatting, e.g. &#39; -> ' (apostrophe)
    match = re.match(r'^(\d*\.?\d+)\s', text) # look for numbers at the start of the string

    if match:
        number_str = match.group(1)
        try:
            val = float(number_str)
            frac = Fraction(val).limit_denominator(16)
            if frac.denominator == 1: # show whole numbers as ints
                formatted_num = str(frac.numerator)
            else:
                formatted_num = f"{frac.numerator}/{frac.denominator}"
            return text.replace(number_str, formatted_num)
        except ValueError:
            pass
    return text

# parses raw JSON data into a formatted string and title
def parse_recipe(recipe_data):
    title = html.unescape(recipe_data.get('name', 'Untitled Recipe'))

    # Extract Publisher/Website Name
    publisher = recipe_data.get('publisher')
    publisher_name = 'Unknown Source'
    
    if publisher:
        if isinstance(publisher, dict):
            publisher_name = publisher.get('name', publisher_name)
        elif isinstance(publisher, str):
            publisher_name = publisher
        elif isinstance(publisher, list) and publisher:
            # Handle list case, taking the first item
            if isinstance(publisher[0], dict):
                publisher_name = publisher[0].get('name', publisher_name)
            elif isinstance(publisher[0], str):
                publisher_name = publisher[0]

    recipe_yield = recipe_data.get('recipeYield', 'N/A') # get yield/serving size
    if isinstance(recipe_yield, list): # sometimes yield is a list, sometimes it's a string
        recipe_yield = ", ".join(recipe_yield)
    else: # just in case the yield is an int/float
        recipe_yield = str(recipe_yield)

    ingredients = recipe_data.get('recipeIngredient', [])
    
    # Instructions can be a list of strings or objects (HowToStep)
    instructions_raw = recipe_data.get('recipeInstructions', [])
    instructions = []
    
    for step in instructions_raw:
        if isinstance(step, str):
            instructions.append(step)
        elif isinstance(step, dict):
            if step.get('@type') == 'HowToStep':
                # 'text' is standard, sometimes 'name' is used
                instructions.append(step.get('text') or step.get('name', ''))
            elif 'text' in step: # Fallback for loosely typed objects
                instructions.append(step['text'])

    # Build output string
    lines = []
    deco = "~*~*~"
    lines.append(f"{deco} {title} {deco}")
    if publisher_name != "Unknown Source":
        lines.append(f"~ Source: {publisher_name} ~")
    lines.append(f"~ Yields: {recipe_yield} ~")
    
    lines.append("\n~ Ingredients ~")
    for ing in ingredients:
        clean_ing = format_ingredient(ing)
        lines.append(f"- {clean_ing}")
        
    lines.append("\n~ Instructions ~")
    for i, step in enumerate(instructions, 1):
        soup_clean = BeautifulSoup(step, "html.parser").get_text() # remove any HTML tags
        clean_step = html.unescape(soup_clean.strip())
        lines.append(f"{i}. {clean_step}")
        
    return title, "\n".join(lines)

# save content to a text file
def save_to_file(title, content):
    # Remove invalid filename characters
    safe_title = re.sub(r'[<>:"/\\|?*]', '', title).strip()
    filename = f"{safe_title}.txt"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Successfully saved to: {filename}")
    except IOError as e:
        print(f"Error saving file: {e}")

if __name__ == "__main__":
    print("~*~ Recipe Extractor ~*~")
    url_input = input("Enter recipe URL: ").strip()
    
    if not url_input:
        print("No URL provided. Exiting...")
    else:
        print("Fetching...")
        try:
            result = get_recipe_data(url_input)
            
            if isinstance(result, dict):
                title, formatted_content = parse_recipe(result)
                print("\n" + formatted_content + "\n")
                save_to_file(title, formatted_content)
            else:
                print(f"Result: {result}")
                
        except requests.exceptions.RequestException as e:
            print(f"Network Error: {e}")
        except Exception as e:
            print(f"Unexpected Error: {e}")
