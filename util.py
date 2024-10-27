import os
import openai
import re
from bs4 import BeautifulSoup, Tag

openai.api_key = os.environ.get("OPENAI_API_KEY")

def call_gpt4(prompt, model="gpt-4o-mini", max_tokens=300, temperature=0.5):
    response = openai.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens, temperature=temperature
    )

    return response.choices[0].message.content

def extract_html_tables(llm_response : str) -> list[Tag]:
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

def extract_table_using_headers(llm_response: str, headers : list[str]) -> Tag:
    
    # find all tables in the response
    tables = extract_html_tables(llm_response=llm_response)
    
    for table in tables:
        current_table_headers = [th.get_text().strip() for th in table.find_all('th')]
        
        if all(header in current_table_headers for header in headers):
            return table
    
    return None

def extract_states_events_table(llm_response):
    states_events_table_headers = ["Current State", "Event", "Next State(s)"]
    states_events_table = extract_table_using_headers(llm_response=llm_response,
                                                      headers=states_events_table_headers)
    return states_events_table

def extract_parallel_states_table(llm_response):
    parallel_states_table_headers = ["Parallel State", "Substate"]
    parallel_states_table = extract_table_using_headers(llm_response=llm_response,
                                                        headers=parallel_states_table_headers)
    return parallel_states_table

def extract_transitions_guards_table(llm_response : str, includeHeader : bool) -> Tag:
    transitions_guards_table_headers = ["From State", "To State", "Event", "Guard"]
    transitions_guards_table = extract_table_using_headers(llm_response=llm_response,
                                                           headers=transitions_guards_table_headers)
    if not includeHeader:
        first_row = transitions_guards_table.find('th')
        if first_row:
            first_row.decompose()
    return transitions_guards_table

def appendTables(table1 : Tag, table2 : Tag) -> Tag:
    for row in table2.find_all('tr'):
        table1.append(row)
    return table1

def extractColumn(table : Tag, column_id : int) -> list[str]:
    column_data = []
    rows = table.find_all('tr')
    for row in rows:
        cells = row.find_all('td')
        if len(cells) > column_id:  # Ensure the row has enough cells
            column_data.append(cells[column_id].get_text())
    return column_data

def extract_transitions_guards_actions_table(llm_response : str) -> Tag:
    transitions_guards_table_events_headers = ["From State", "To State", "Event", "Guard", "Entry Action", "Exit Action"]
    transitions_guards_actions_table = extract_table_using_headers(llm_response=llm_response,
                                                                   headers=transitions_guards_table_events_headers)
    return transitions_guards_actions_table
    