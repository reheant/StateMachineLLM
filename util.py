import os
import openai
import re
from bs4 import BeautifulSoup, Tag

openai.api_key = os.environ.get("OPENAI_API_KEY")

def call_gpt4(prompt, model="gpt-4o-mini", max_tokens=300, temperature=1):
    response = openai.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature
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
    if not includeHeader and transitions_guards_table:
        first_row = transitions_guards_table.find('th')
        if first_row:
            first_row.decompose()
    return transitions_guards_table

def extract_history_state_table(llm_response : str, includeHeader: bool) -> Tag:
    history_table_headers = ["From State", "Event", "Guard", "Action"]
    history_table = extract_table_using_headers(llm_response=llm_response,
                                                           headers=history_table_headers)
    if not includeHeader and history_table:
        first_row = history_table.find('th')
        if first_row:
            first_row.decompose()
    return history_table

def extract_hierarchical_state_table(llm_response : str) -> Tag:
    history_table_headers = ["Superstate", "Substate"]
    history_table = extract_table_using_headers(llm_response=llm_response,
                                                headers=history_table_headers)
    return history_table

def appendTables(table1 : Tag, table2 : Tag) -> Tag:
    for row in table2.find_all('tr'):
        table1.append(row)
    return table1

def addColumn(table : Tag, headerName : str, columnIdx : int, placeholderValue : str):
    soup = BeautifulSoup(str(table), 'html.parser')

    # Add a new header for the new column
    if headerName:
        new_header = soup.new_tag('th')
        new_header.string = headerName
        header_row = table.find('tr')
        header_row.insert(columnIdx, new_header)

    # Add new column data to each row
    for row in table.find_all('tr')[1 if headerName else 0:]:  # Skip the header row
        new_col = soup.new_tag('td')
        new_col.string = placeholderValue
        row.insert(columnIdx, new_col)

    return table

def extractColumn(table : Tag, columnIdx : int):
    column_list = []
    # soup = BeautifulSoup(str(table), 'html.parser')

    # # Find the table
    # table = soup.find('table', {'id': 'myTable'})

    # Add new column data to each row
    for row in table.find_all('tr')[1:]:  # Skip the header row=
        cols = row.find_all('td')
        column_list.append(cols[columnIdx].get_text())

    return column_list

def extract_transitions_guards_actions_table(llm_response : str) -> Tag:
    transitions_guards_table_events_headers = ["From State", "To State", "Event", "Guard", "Action"]
    transitions_guards_actions_table = extract_table_using_headers(llm_response=llm_response,
                                                                   headers=transitions_guards_table_events_headers)
    return transitions_guards_actions_table
    