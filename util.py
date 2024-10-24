import os
import openai
import re
from bs4 import BeautifulSoup

openai.api_key = os.environ.get("OPENAI_API_KEY")

def call_gpt4(prompt, model="gpt-4", max_tokens=150, temperature=0.7):
    response = openai.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content

def extract_html_tables_from_code(html_string):
    # extract the content within the ```html code blocks using regex
    code_blocks = re.findall(r'```html(.*?)```', html_string, re.DOTALL)
    
    tables = []
    
    # for each HTML code block, parse and extract the tables
    for block in code_blocks:
        # parse the HTML content
        soup = BeautifulSoup(block, 'html.parser')
        
        # find all <table> elements from parsed elements
        table_elements = soup.find_all('table')
        
        # extract each table's HTML and add to list of tables
        for table in table_elements:
            tables.append(str(table))
    
    return tables