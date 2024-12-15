import os
import anthropic
import groq
import openai
from openai import OpenAI
import re
from bs4 import BeautifulSoup, Tag
from transitions.extensions import HierarchicalGraphMachine
import mermaid as md
from mermaid.graph import Graph
from sherpa_ai.memory.state_machine import SherpaStateMachine
from getpass import getpass
import aisuite as ai
from ecologits import EcoLogits
from resources.environmental_impact.impact_tracker import tracker



openai.api_key = os.environ.get("OPENAI_API_KEY")
groq.api_key = os.environ.get("GROQ_API_KEY")
anthropic.api_key = os.environ.get("ANTHROPIC_API_KEY")


EcoLogits.init(providers="openai")
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

client = ai.Client()


def choose_model():
    print("Please pick the model you want to use to power your assistant:")
    print("1. GPT-4o")
    print("2. Claude 3.5 Sonnet")
    print("3. Llama 3.2 3b Preview")
    print("4. Gemini 1.5 Pro 001")


    while True:
        try:
            choice = int(input("Enter the number corresponding to your model (1, 2, 3, 4): "))
            if choice == 1:
                return "openai:gpt-4o"
            elif choice == 2:
                return  "anthropic:claude-3-5-sonnet-20241022"
            elif choice == 3:
                return "groq:llama-3.2-3b-preview"
            elif choice == 4:
                return "google:gemini-1.5-pro-001"
            else:
                print("Invalid choice. Please enter 1, 2, 3 or 4.")
        except ValueError:
            print("Invalid input. Please enter a number (1, 2, 3, or 4).")

model = choose_model()

def call_llm(prompt, max_tokens=1200, temperature=0.7):
    """
    The call_llm function calls the specified LLM with a specified prompt,
    max_tokens, and temperature, and returns the string response of the LLM
    """
    global energy_consumed, carbon_emissions, abiotic_resource_depletion

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": "You are a programming assistant specialized in generating HTML content. Your task is to create a state machine representation using HTML tables."},
                  {"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=max_tokens
    )

    if model == "openai:gpt-4o":
        tracker.update_impacts(response)

    return str (response.choices[0].message.content)


if __name__ == "__main__":
    prompt = "Hi, I need help answering a question about states machines. What are events?"
    model="google:gemini-1.5-pro-001"
    llm_response = call_llm(prompt)
    print(llm_response)

    
def extract_html_tables(llm_response : str) -> list[Tag]:
    """
    The extract HTML tables function takes in a string representing
    the LLM's response, and extracts all HTML tables in the response.
    A list of BeautifulSoup tags are returned so tables can be further
    processed
    """
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
    """
    The extract_table_using_headers function extracts all tables with the matching list
    of headers from an LLM response, and returns a BeautifulSoup tag containing the table
    """
    # find all tables in the response
    tables = extract_html_tables(llm_response=llm_response)
    
    for table in tables:
        current_table_headers = [th.get_text().strip() for th in table.find_all('th')]
        
        if all(header in current_table_headers for header in headers):
            return table
    
    return None

def extract_states_events_table(llm_response):
    """
    Extract the states-events table for Linear SMF responses
    """
    states_events_table_headers = ["Current State", "Event", "Next State(s)"]
    states_events_table = extract_table_using_headers(llm_response=llm_response,
                                                      headers=states_events_table_headers)
    return states_events_table

def extract_parallel_states_table(llm_response):
    """
    Extracts the parallel states table for Linear SMF responses
    """
    parallel_states_table_headers = ["Parallel State", "Substate"]
    parallel_states_table = extract_table_using_headers(llm_response=llm_response,
                                                        headers=parallel_states_table_headers)
    return parallel_states_table

def extract_transitions_guards_table(llm_response : str, includeHeader : bool) -> Tag:
    """
    Extracts the table of transitions with headers "From State", "To State", "Event",
    and "Guard" for Linear SMF responses
    """
    transitions_guards_table_headers = ["From State", "To State", "Event", "Guard"]
    transitions_guards_table = extract_table_using_headers(llm_response=llm_response,
                                                           headers=transitions_guards_table_headers)
    if not includeHeader and transitions_guards_table:
        first_row = transitions_guards_table.find('th')
        if first_row:
            first_row.decompose()
    return transitions_guards_table

def extract_history_state_table(llm_response : str, includeHeader: bool = False) -> Tag:
    """
    Extracts the table containing history state transitions for History States for
    Linear SMF responses
    """
    history_table_headers = ["From State", "Event", "Guard", "Action"]
    history_table = extract_table_using_headers(llm_response=llm_response,
                                                headers=history_table_headers)
    if history_table and not includeHeader:
        first_row = history_table.find('tr')
        if first_row:
            first_row.decompose()
    return history_table

def extract_hierarchical_state_table(llm_response : str) -> Tag:
    """
    Extracts tables depicting Hierarchical State relationships in
    responses for Event Driven SMF responses
    """
    history_table_headers = ["Superstate", "Substate"]
    history_table = extract_table_using_headers(llm_response=llm_response,
                                                headers=history_table_headers)
    return history_table

def appendTables(table1 : Tag, table2 : Tag) -> Tag:
    """
    The appendTables function merges the rows of two tables together (assuming
    the two tables have the same headers)
    """
    table1 = BeautifulSoup(str(table1), 'html.parser').find_all('table')[0]
    table2 = BeautifulSoup(str(table2), 'html.parser').find_all('table')[0]

    for row in table2.find_all('tr'):
        table1.append(row)
    return table1

def addColumn(table : Tag, headerName : str, columnIdx : int, placeholderValue : str):
    """
    The addColumn function adds a new column to a given table at the specified index,
    with the header headerName, and a default value placeholderValue
    """
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
    """
    The extractColumn gets all entries in the column at index
    columnIdx
    """
    column_list = []

    # Add new column data to each row
    if table:
        for row in table.find_all('tr')[1:]:  # Skip the header row=
            cols = row.find_all('td')
            column_list.append(cols[columnIdx].get_text())

    return column_list

def extract_transitions_guards_actions_table(llm_response : str) -> Tag:
    """
    Extracts transitions tables with headers "From State", "To State", "Event", "Guard", and
    "Action" for Linear SMF and Event Driven SMF responses
    """
    transitions_guards_table_events_headers = ["From State", "To State", "Event", "Guard", "Action"]
    transitions_guards_actions_table = extract_table_using_headers(llm_response=llm_response,
                                                                   headers=transitions_guards_table_events_headers)
    return transitions_guards_actions_table
    
def str_to_Tag(table : str):
    """
    converts the string of an HTML table into a BeautifulSoup Tag
    """
    tables = BeautifulSoup(str(table), 'html.parser').find_all('table')
    return tables[0] if tables else None

def format_state_name_for_pytransitions(state_name, hierarchical_states_table):
    """
    given a state name and the table of hierarchical states, format the state's name to be the expected
    format for the transitions for pytransitions. The format is ParentState_ChildState
    """
    child_state_to_parent_state = map_child_state_to_parent_state(hierarchical_state_table=hierarchical_states_table)
    if child_state_to_parent_state and child_state_to_parent_state.get(state_name, None) is not None:
        return f"{child_state_to_parent_state.get(state_name)}_{state_name}"
    else:
        return state_name

def gsm_tables_to_dict(hierarchical_states_table : Tag, transitions_table : Tag, parallel_state_table : Tag):
    """
    Extracts the states, transitions, and parallel regions of a Generated State Machine (GSM) and returns
    them in a list
    """
    hierarchical_states_table = table_remove_spaces(str_to_Tag(hierarchical_states_table))
    transitions_table = table_remove_spaces(str_to_Tag(transitions_table))
    parallel_state_table = table_remove_spaces(str_to_Tag(parallel_state_table))
    states = []
    transitions = []
    parallel_regions = []

    # Add states to state list
    states += list(set(extractColumn(hierarchical_states_table, 0) + extractColumn(hierarchical_states_table, 1) + extractColumn(transitions_table, 0) + extractColumn(transitions_table, 1) + extractColumn(parallel_state_table, 1)))

    for row in transitions_table.find_all('tr')[1:]:  # Skip the header row=
        cols = row.find_all('td')
        transition = {
            "trigger": cols[2].get_text(),
            "source": format_state_name_for_pytransitions(state_name=cols[0].get_text(), hierarchical_states_table=hierarchical_states_table),
            "dest": format_state_name_for_pytransitions(state_name=cols[1].get_text(), hierarchical_states_table=hierarchical_states_table),
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

    # States under '-' really don't have a superstate
    non_composite_state = [state for state in states if isinstance(state, dict) and state['name'] == '-']
    if non_composite_state:
        for child in non_composite_state[0]['children']:
            if child not in states:
                states.append(child)
        states.remove(non_composite_state[0])

    # remove states which are already encompassed by a parent state
    states = [state for state in states if (non_composite_state and state in non_composite_state[0]["children"]) or isinstance(state, dict)]

    # Remove all spaces not to confuse mermaid
    states = list(map(state_remove_spaces, states))
    transitions = list(map(transitions_remove_spaces, transitions))
    parallel_regions = list(map(regions_remove_spaces, parallel_regions))

    return states, transitions, parallel_regions

def add_initial_hierarchical_states(gsm_states : list, hierarchical_initial_states : dict):
    """
    the add_initial_hierarchical_states sets the "initial" key of the hierarchical states in the gsm_states
    list to map to the name of the hierarchical state's initial state, as required by pytransitions. note
    that the initial state name does NOT need to be in the format "ParentState_ChildState"
    """

    # iterate over each hierarchical state and its initial state
    for hierarchical_state_name, initial_state_name in hierarchical_initial_states.items():
        if initial_state_name is not None:
            # locate the hierarchical state in the list of initial states
            for gsm_state in gsm_states:
                # check to see if the current state is the hierarchical state and set the initial state if it is one of the child states
                if isinstance(gsm_state, dict) and gsm_state.get("name") == hierarchical_state_name.replace(" ", "") and initial_state_name.replace(" ", "") in gsm_state.get("children"):
                    gsm_state["initial"] = initial_state_name.replace(" ", "")
                    break

    return gsm_states

def create_event_based_gsm_diagram(hierarchical_states_table : Tag, transitions_table : Tag, parallel_state_table : Tag, initial_state : str, hierarchical_initial_states : dict):
    gsm_states, gsm_transitions, gsm_parallel_regions = gsm_tables_to_dict(hierarchical_states_table=hierarchical_states_table,
                                                                           transitions_table=transitions_table,
                                                                           parallel_state_table=parallel_state_table)
    
    # update the states so each hierarchical state contains their initial state
    gsm_states = add_initial_hierarchical_states(gsm_states=gsm_states,
                                                 hierarchical_initial_states=hierarchical_initial_states)
    print(f"States: {gsm_states}")
    print(f"Transitions: {gsm_transitions}")
    print(f"Parallel Regions: {gsm_parallel_regions}")

    # Create the state machine
    gsm = SherpaStateMachine(
        states=gsm_states,
        transitions=gsm_transitions,
        initial=format_state_name_for_pytransitions(initial_state, hierarchical_states_table=hierarchical_states_table).replace(" ", ""),
        sm_cls=HierarchicalGraphMachine
    )
    
    print(gsm.sm.get_graph().draw(None))

    # Generate and render a sequence diagram
    sequence = Graph('Sequence-diagram', gsm.sm.get_graph().draw(None))
    render = md.Mermaid(sequence)
    render.to_png('ExhibitA.png')

def table_remove_spaces(table):
    """
    Removes white space from table entries
    """
    if not table:
        return None
    
    # Find all table cells
    cells = table.find_all('td')

    # Iterate through each cell and remove spaces
    for cell in cells:
        cell.string = cell.get_text().replace(' ','')

    return table

def state_remove_spaces(state):
    """
    Removes white space from State Table entries
    """

    # the state is a hierarchical state
    if isinstance(state, dict):
        state['name'] = state['name'].replace(' ', '')
        state['children'] = [s.replace(' ', '') for s in state['children']]
    else:
        # the state is not a hierarchical state
        state = state.replace(' ', '')
    return state

def transitions_remove_spaces(transition):
    """
    Removes white space from state names in a transition dictionary
    """
    transition['source'] = transition['source'].replace(' ', '')
    transition['dest'] = transition['dest'].replace(' ', '')
    return transition

def regions_remove_spaces(region):
    """
    Removes the white space from parallel region and region child states in a region dictionary
    """
    region['name'] = region['name'].replace(' ', '')
    region['regionChildren'] = [s.replace(' ', '') for s in region['regionChildren']]
    return region

def extract_event_driven_states_table(llm_response : str) -> Tag:
    """
    Extracts the table containing all states of a UML State Machine for Event Driven SMF responses
    """
    event_driven_states_table_headers = ["StateName"]
    event_driven_states_table = extract_table_using_headers(llm_response=llm_response,
                                                            headers=event_driven_states_table_headers)
    return event_driven_states_table

def extract_event_driven_events_table(llm_response : str) -> Tag:
    """
    Extracts the table containing all events of a UML State Machine for Event Driven SMF responses
    """
    event_driven_events_table_headers = ["EventName"]
    event_driven_events_table = extract_table_using_headers(llm_response=llm_response,
                                                            headers=event_driven_events_table_headers)
    return event_driven_events_table


def extract_table_entries(table: Tag):
    """
    Extracts all table entries in a given BeautifulSoup table
    """
    table = str(table)
    soup = BeautifulSoup(table, "html.parser")
    table = soup.find("table")
    entries = [td.get_text(strip=True) for td in table.find_all("td")]
    return entries

def merge_tables(html_tables_list) -> Tag:
    """
    Appends a list of HTML tables together, assuming all tables in the list
    have the exact same headers and columns
    """
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

def create_exit_transitions_table(transitions_table, from_state):
    """
    Using the transitions table of the entire UML State Machine, given
    the starting state from_state, return a table of all transitions exiting
    the state, with each row having a unique ID
    """

    # Parse the transitions table
    transitions_table = str(transitions_table)
    soup = BeautifulSoup(transitions_table, "html.parser")
    transitions_table = soup.find("table")
    rows = transitions_table.find_all("tr")

    # Create a new table for filtered transitions
    from_state_transitions_table = BeautifulSoup("<table border='1'></table>", "html.parser")
    from_state_transitions_table_table = from_state_transitions_table.table

    # Add a new "Transition ID" column to the header row
    header_row = rows[0]
    header_columns = header_row.find_all("th")
    header_row.append(soup.new_tag("th"))  # Add a new <th> for "Transition ID"
    header_row.find_all("th")[-1].string = "Transition ID"
    from_state_transitions_table_table.append(header_row)

    id = 1
    for row in rows[1:]:
        columns = row.find_all("td")
        if columns[0].get_text(strip=True) == from_state:
            # create a new row with the unique ID
            new_row = BeautifulSoup(str(row), "html.parser").tr
            new_transition_id = soup.new_tag("td")
            new_transition_id.string = str(id)
            id += 1
            new_row.append(new_transition_id)
            from_state_transitions_table_table.append(new_row)

    return from_state_transitions_table

def remove_transitions_from_exit_transition_table(transitions_table, ids_to_remove):
    """
    Given a list of transition IDs ids_to_remove, the remove_transitions_from_exit_transition_table
    removes all transitions that have their ID in the list ids_to_remove
    """
    transitions_table = str(transitions_table)
    soup = BeautifulSoup(transitions_table, "html.parser")
    transitions_table = soup.find("table")

    rows = transitions_table.find_all("tr")

    for row in rows[1:]:
        columns = row.find_all("td")
        transition_id = columns[5].get_text(strip=True)
        if transition_id in ids_to_remove:
            row.decompose()

    # remove the ID column and its entries afterwards
    header_row = transitions_table.find("tr")
    if header_row:
        header_cells = header_row.find_all("th")
        header_cells[5].decompose()
    
    rows = transitions_table.find_all("tr")
    for row in rows[1:]:
        columns = row.find_all("td")
        id_column = columns[5]
        id_column.decompose()
    
    return transitions_table


def group_parent_child_states(hierarchical_state_table):
    """
    Given the hierarchical state table with columns "Superstate" and "Substate",
    create a dictionary mapping each Superstate to a list of its Substates
    """
    if isinstance(hierarchical_state_table, str):
        soup = BeautifulSoup(hierarchical_state_table, "html.parser")
        hierarchical_state_table = soup.find("table")

    hierarchical_state_dict = {}

    # extract all rows except for header
    rows = hierarchical_state_table.find_all("tr")[1:]

    for row in rows:
        cells = row.find_all("td")
        parent_state = cells[0].get_text(strip=True)
        child_state = cells[1].get_text(strip=True)
        
        # we're only concerned about hierarchical states
        if parent_state != "-":
            if parent_state not in hierarchical_state_dict:
                hierarchical_state_dict[parent_state] = []

            # add the current child state to the list of child states in the dict
            hierarchical_state_dict[parent_state].append(child_state)
    
    return hierarchical_state_dict

def map_child_state_to_parent_state(hierarchical_state_table):
    """
    Given the hierarchical state table with columns "Superstate" and "Substate",
    create a dictionary mapping each Substate to its Superstate, if it has one
    """
    hierarchical_state_table = str(hierarchical_state_table)
    soup = BeautifulSoup(hierarchical_state_table, "html.parser")
    hierarchical_state_table = soup.find("table")

    child_to_parent_dict = {}

    # extract all rows except for header
    rows = hierarchical_state_table.find_all("tr")[1:]

    for row in rows:
        cells = row.find_all("td")
        parent_state = cells[0].get_text(strip=True)
        child_state = cells[1].get_text(strip=True)
        
        # only create mappings for states that actually have a parent in the hierarchy
        if parent_state != "-":
            child_to_parent_dict[child_state] = parent_state
    
    return child_to_parent_dict

def refactor_transition_table_with_parent_states(transitions_table, hierarchical_state_table):
    """
    Replaces the "From State" and "To State" columns with states named in the format ParentState.ChildState
    """

    # map each child state to its parent, if it has one
    child_to_parent_dict = map_child_state_to_parent_state(hierarchical_state_table=hierarchical_state_table)

    # convert to beautiful soup if input is a string
    transitions_table = str(transitions_table)
    soup = BeautifulSoup(transitions_table, "html.parser")
    transitions_table = soup.find("table")

    # iterate over each row in the transitions table
    rows = transitions_table.find_all("tr")[1:]

    for row in rows:
        cells = row.find_all("td")
        from_state = cells[0].get_text(strip=True)
        to_state = cells[1].get_text(strip=True)

        # replace "From State" with "Parent.Child" format if parent exists in child_to_parent_dict
        if from_state in child_to_parent_dict:
            parent = child_to_parent_dict[from_state]
            formatted_from_state = f"{parent}.{from_state}"
        else:
            formatted_from_state = from_state

        # replace "To State" with "Parent.Child" format if parent exists in child_to_parent_dict
        if to_state in child_to_parent_dict:
            parent = child_to_parent_dict[to_state]
            formatted_to_state = f"{parent}.{to_state}"
        else:
            formatted_to_state = to_state

        # update the cell text with the formatted state names
        cells[0].string = formatted_from_state
        cells[1].string = formatted_to_state

    return transitions_table

def find_events_for_transitions_table(transitions_table):
    """
    Extracts all the events that occur in a given HTML transitions table
    """
    # convert to beautiful soup if input is a string
    transitions_table = str(transitions_table)
    soup = BeautifulSoup(transitions_table, "html.parser")
    transitions_table = soup.find("table")

    # iterate over each row in the transitions table
    rows = transitions_table.find_all("tr")[1:]

    events = set()

    for row in rows:
        cells = row.find_all("td")
        event = cells[2].get_text(strip=True)
        events.add(event)

    return list(events) 

def parse_html_table(html_table):
    soup = BeautifulSoup(html_table, 'html.parser')
    table = soup.find('table')

    headers = []
    header_row = table.find('tr')
    if header_row:
        for th in header_row.find_all('th'):
            header = th.get_text(strip=True)
            headers.append(header)
    else:
        first_row = table.find('tr')
        num_columns = len(first_row.find_all(['th', 'td']))
        headers = ['Column {}'.format(i+1) for i in range(num_columns)]

    data = []

    for row in table.find_all('tr')[1:]:
        cols = row.find_all('td')
        if len(cols) != len(headers):
            continue
        row_data = {}
        for idx, col in enumerate(cols):
            cell_data = col.get_text(strip=True)
            row_data[headers[idx]] = cell_data
        data.append(row_data)

    return data

def dict_to_html_table(data):
    if not data:
        return "<table></table>"

    headers = data[0].keys()
    
    html = "<table border='1'>\n"
    
    html += "  <tr>\n"
    for header in headers:
        html += f"    <th>{header}</th>\n"
    html += "  </tr>\n"

    for row in data:
        html += "  <tr>\n"
        for header in headers:
            html += f"    <td>{row.get(header, '')}</td>\n"
        html += "  </tr>\n"
    
    html += "</table>"
    return html

def getStateHierarchyDictFromList(state_hierarchy_list):
    hierarchy = {}
    for entry in state_hierarchy_list:
        superstate = entry['Superstate']
        substate = entry['Substate']
        if superstate != '-':
            if superstate not in hierarchy:
                hierarchy[superstate] = []
            hierarchy[superstate].append(substate)
    
    return hierarchy
