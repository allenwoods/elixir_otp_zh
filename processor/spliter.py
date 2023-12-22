from pathlib import Path
import ebooklib
from ebooklib import epub
import os
import markdown2
import bs4

SRC_EPUB = Path(__file__).parent.parent / "elixir_otp.epub"
TAR_DIR = Path(__file__).parent.parent / "elixir_otp"

# Function to convert HTML to Markdown
def html_to_markdown(html_content):
    # Convert HTML to Markdown
    markdown_content = markdown2.markdown(html_content)
    return markdown_content

# Function to create directories and save markdown files
def save_markdown_files(markdown_structure, base_path):
    for part in markdown_structure:
        part_path = os.path.join(base_path, part.replace(" ", "_"))
        os.makedirs(part_path, exist_ok=True)
        for chapter in markdown_structure[part]:
            chapter_file_name = f"{chapter.replace(' ', '_')}.md"
            chapter_path = os.path.join(part_path, chapter_file_name)
            with open(chapter_path, 'w') as file:
                file.write(markdown_structure[part][chapter])

# Load the EPUB file
book = epub.read_epub(SRC_EPUB)

# Extracting and structuring content
markdown_structure = {}
current_part = None

for item in book.get_items():
    if item.get_type() == ebooklib.ITEM_DOCUMENT:
        soup = bs4.BeautifulSoup(item.content, 'html.parser')
        title = str(soup.title.string) if soup.title else 'Untitled'
        print(title)
        
        if 'Part' in title:
            current_part = title
            markdown_structure[current_part] = {}
        elif current_part:
            markdown_structure[current_part][title] = html_to_markdown(str(soup))

# Create base directory for markdown files
base_path = TAR_DIR
os.makedirs(base_path)

# Save markdown files
save_markdown_files(markdown_structure, base_path)
