import os
import openai
import re
from bs4 import BeautifulSoup, Tag

openai.api_key = os.environ.get("OPENAI_API_KEY")

def call_gpt4(prompt, model="gpt-4o", max_tokens=1200, temperature=0.7):
    response = openai.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=max_tokens
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
    if table:
        for row in table.find_all('tr')[1:]:  # Skip the header row=
            cols = row.find_all('td')
            column_list.append(cols[columnIdx].get_text())

    return column_list

def extract_transitions_guards_actions_table(llm_response : str) -> Tag:
    transitions_guards_table_events_headers = ["From State", "To State", "Event", "Guard", "Action"]
    transitions_guards_actions_table = extract_table_using_headers(llm_response=llm_response,
                                                                   headers=transitions_guards_table_events_headers)
    return transitions_guards_actions_table
    
def gsm_tables_to_dict(hierarchical_states_table : Tag, transitions_table : Tag, parallel_state_table : Tag):
    states = []
    transitions = []
    parallel_regions = []

    # Add states to state list
    states += list(set(extractColumn(hierarchical_states_table, 0) + extractColumn(hierarchical_states_table, 1) + extractColumn(transitions_table, 0) + extractColumn(transitions_table, 1) + extractColumn(parallel_state_table, 1)))

    for row in transitions_table.find_all('tr')[1:]:  # Skip the header row=
        cols = row.find_all('td')
        transition = {
            "trigger": cols[2].get_text(),
            "source": cols[0].get_text(),
            "dest": cols[1].get_text(),
        }
        if (cols[4].get_text() != "NONE"):
            transition["before"] = cols[4].get_text()
        if (cols[3].get_text() != "NONE"):
            transition["conditions"] = cols[3].get_text()
        
        transitions.append(transition)
    
    if hierarchical_states_table:
        for row in hierarchical_states_table.find_all('tr')[1:]:  # Skip the header row=
            cols = row.find_all('td')

            try:
                stateIdx = states.index(cols[0].get_text())
            except ValueError:
                stateIdx = [states.index(dic) for dic in states if isinstance(dic, dict) and dic['name'] == cols[0].get_text()][0]

            if not isinstance(states[stateIdx], dict):
                hierarchical_state = {
                    "name": cols[0].get_text(),
                    "children": [cols[1].get_text()]
                }
                states[stateIdx] = hierarchical_state
            else:
                states[stateIdx]['children'].append(cols[1].get_text())
    
    if parallel_state_table:
        for row in parallel_state_table.find_all('tr')[1:]:  # Skip the header row=
            cols = row.find_all('td')

            region = [parallel_regions.index(dic) for dic in parallel_regions if isinstance(dic, dict) and dic['name'] == cols[0].get_text()]

            if not region:
                region = {
                    "name": cols[0].get_text(),
                    "regionChildren": [cols[1].get_text()]
                }
                parallel_regions[region[0]] = region
            else:
                parallel_regions[region[0]]['regionChildren'].append(cols[1].get_text())

    # Remove all spaces not to confuse mermaid
    states = list(map(state_remove_spaces, states))
    transitions = list(map(transitions_remove_spaces, transitions))
    parallel_regions = list(map(regions_remove_spaces, parallel_regions))

    return states, transitions, parallel_regions

def state_remove_spaces(state):
    if isinstance(state, dict):
        state['name'] = state['name'].replace(' ', '')
        state['children'] = [s.replace(' ', '') for s in state['children']]
    else:
        state = state.replace(' ', '')
    return state

def transitions_remove_spaces(transition):
    transition['source'] = transition['source'].replace(' ', '')
    transition['dest'] = transition['dest'].replace(' ', '')
    return transition

def regions_remove_spaces(region):
    region['name'] = region['name'].replace(' ', '')
    region['regionChildren'] = [s.replace(' ', '') for s in region['regionChildren']]
    return region

def extract_event_driven_states_table(llm_response : str) -> Tag:
    event_driven_states_table_headers = ["State Name"]
    event_driven_states_table = extract_table_using_headers(llm_response=llm_response,
                                                            headers=event_driven_states_table_headers)
    return event_driven_states_table

def extract_event_driven_events_table(llm_response : str) -> Tag:
    event_driven_events_table_headers = ["Event Name"]
    event_driven_events_table = extract_table_using_headers(llm_response=llm_response,
                                                            headers=event_driven_events_table_headers)
    return event_driven_events_table

def extract_table_entries(table: Tag):
    entries = [td.get_text(strip=True) for td in table.find_all("td")]
    return entries

def merge_tables(html_tables_list) -> Tag:
    # Assume the first table contains the header, so extract it
    header_cells = [th.get_text() for th in html_tables_list[0].find_all('th')]

    # Create a new BeautifulSoup object with an empty table for merging
    merged_table_soup = BeautifulSoup("<table border='1'><tr></tr></table>", 'html.parser')
    merged_table = merged_table_soup.find('table')

    # Create header row in the merged table
    header_row = merged_table.find('tr')
    for header in header_cells:
        th = merged_table_soup.new_tag('th')
        th.string = header
        header_row.append(th)

    # Collect all rows from each table and add them to the merged table
    for table_tag in html_tables_list:
        rows = table_tag.find_all('tr')[1:]  # Skip the header row

        for row in rows:
            new_row = merged_table_soup.new_tag('tr')
            for cell in row.find_all('td'):
                new_cell = merged_table_soup.new_tag('td')
                new_cell.string = cell.get_text()
                new_row.append(new_cell)
            merged_table.append(new_row)

    # Return the <table> Tag object directly
    return merged_table
    
