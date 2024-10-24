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

def extract_html_tables_from_llm_response(llm_response):
    # extract the content within the ```html code blocks using regex
    code_blocks = re.findall(r'```html(.*?)```', llm_response, re.DOTALL)
    
    tables = []
    
    # for each HTML code block, parse and extract the tables
    for block in code_blocks:
        # parse the HTML content
        soup = BeautifulSoup(block, 'html.parser')
        
        # find all <table> elements from parsed elements
        table_elements = soup.find_all('table')
        
        # extract each table's HTML and add to list of tables
        for table in table_elements:
            tables.append(table)
    
    return tables

def extract_states_events_table_from_llm_response(llm_response):
    
    states_events_table_headers = ["Current State",
                                   "Event",
                                   "Next State(s)"]
    
    # find all tables in the response
    tables = extract_html_tables_from_llm_response(llm_response=llm_response)
    
    for table in tables:
        current_table_headers = [th.get_text().strip() for th in table.find_all('th')]
        
        if all(header in current_table_headers for header in states_events_table_headers):
            return str(table)
    
    return None
    