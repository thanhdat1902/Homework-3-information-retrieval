from pymongo import MongoClient
from bs4 import BeautifulSoup
import re
# MongoDB setup
client = MongoClient("mongodb://localhost:27017/")
db = client["CPPCrawler"]
pages_collection = db["pages"]
professors_collection = db["professors"]

def parse_professor_details(soup):
    # Initialize a dictionary to hold the parsed details
    professor_info = {
        "title": None,
        "office": None,
        "phone": None,
        "email": None,
        "website": None
    }

    # Extract all <strong> tags and the associated data
    strong_tags = soup.find_all('strong')

    # Cleaned labels for comparison (ignoring colons)
    label_mapping = {
        "title": "Title",
        "office": "Office",
        "phone": "Phone",
        "email": "Email",
        "website": "Web"
    }

    for strong in strong_tags:
        label_text = strong.get_text(strip=True).replace(":", "")  # Remove colon for comparison
        for key, value in label_mapping.items():
            # Normalize comparison by stripping spaces and checking for exact match
            if value.lower() == label_text.lower():
                next_sibling = strong.find_next_sibling(string=True)  # Get the value associated with the label
                if next_sibling:
                    professor_info[key] = next_sibling.strip().lstrip(":").strip()

                # Special handling for email and website (they are inside <a> tags)
                if key == "email":
                    email_tag = strong.find_next_sibling('a')  # Directly find the <a> tag
                    if email_tag:
                        professor_info["email"] = email_tag.get_text(strip=True)
                elif key == "website":
                    web_tag = strong.find_next_sibling('a')  # Directly find the <a> tag
                    if web_tag:
                        professor_info["website"] = web_tag.get('href', '').strip()

    return professor_info

def parse_professors(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    professor_list = []

    # Locate the main section
    main_section = soup.find('div', id='main')
    if not main_section:
        return []  # Return empty if main section is not found
    # Ensure it contains 'Permanent Faculty'
    faculty_header = main_section.find('h1', string=re.compile(r'Permanent\s+Faculty', re.IGNORECASE))

    if not faculty_header:
        return []  # Return empty if 'Permanent Faculty' is not found

    for prof_div in main_section.find_all('div'):
        # Find all professor's details in the div (i.e., both img, h2, and p)
        img_tags = prof_div.find_all('img')
        h2_tags = prof_div.find_all('h2')
        p_tags = prof_div.find_all('p')

        # Ensure we have at least one image, h2, and p tag
        if len(h2_tags) > 0 and len(p_tags) > 0:
            for i in range(len(h2_tags)):
                # Extract professor's name
                name = h2_tags[i].get_text(strip=True)

                # Extract the corresponding details (assumes that p_tags are in order)
                details = p_tags[i]

                # Parse the professor details
                professor = parse_professor_details(details)

                # Add the professor to the list
                professor_list.append({"name": name, **professor})

    return professor_list

def store_professors(professors):
    for professor in professors:
        professors_collection.insert_one(professor)
    print(f"Stored {len(professors)} professors in the database.")

def main():
    # Retrieve the "Permanent Faculty" page HTML from the pages collection
    target_page = pages_collection.find_one({"url": "https://www.cpp.edu/sci/computer-science/faculty-and-staff/permanent-faculty.shtml"})
    if not target_page:
        print("Permanent Faculty page not found in the database.")
        return

    html = target_page["html"]
    professors = parse_professors(html)

    if professors:
        store_professors(professors)
    else:
        print("No professors data parsed.")

if __name__ == "__main__":
    main()
