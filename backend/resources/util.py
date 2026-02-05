import os
import graphviz
import re
import subprocess
import time
import requests
from bs4 import BeautifulSoup, Tag
from transitions.extensions import HierarchicalGraphMachine
import mermaid as md
from mermaid.graph import Graph
from sherpa_ai.memory.state_machine import SherpaStateMachine
from .llm_tracker import llm

# OpenRouter API key for single prompt
openrouter_api_key = os.environ.get("OPENROUTER_API_KEY")


def choose_model():
    """Function that inquires the user for the model"""
    print("Please pick the model you want to use to power your assistant:")
    print("1. GPT-4o")
    print("2. Claude 3.5 Sonnet")
    print("3. Llama 3.2 3b Preview")
    print("4. Gemini 1.5 Pro 001")

    while True:
        try:
            choice = int(
                input("Enter the number corresponding to your model (1, 2, 3, 4): ")
            )
            if choice == 1:
                return "openai:gpt-4o"
            elif choice == 2:
                return "anthropic:claude-3-5-sonnet-20241022"
            elif choice == 3:
                return "groq:llama-3.2-3b-preview"
            elif choice == 4:
                return "google:gemini-1.5-pro-001"
            else:
                print("Invalid choice. Please enter 1, 2, 3 or 4.")
        except ValueError:
            print("Invalid input. Please enter a number (1, 2, 3, or 4).")


def call_llm(prompt, max_tokens=1200, temperature=0.7):
    """
    The call_llm function calls the specified LLM with a specified prompt,
    max_tokens, and temperature, and returns the string response of the LLM

    NOTE: This function requires additional dependencies (aisuite, openai, anthropic, groq).
    For single prompt approach, use call_openrouter_llm instead.
    """
    raise NotImplementedError(
        "call_llm requires additional dependencies (aisuite, openai, anthropic, groq). "
        "Please use the single prompt approach with call_openrouter_llm, or install the full dependencies."
    )


def call_openrouter_llm(
    prompt, max_tokens=1500, temperature=0.7, model="anthropic/claude-3.5-sonnet"
):
    """
    Call OpenRouter API for LLM requests specifically for single prompt technique
    """
    import requests

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {openrouter_api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/ECSE458-Multi-Agent-LLM/StateMachineLLM",
        "X-Title": "StateMachineLLM Single Prompt",
    }

    data = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You are an AI assistant specialized in generating state machines using Mermaid stateDiagram-v2 syntax. Analyze problem descriptions and generate complete UML state machines with states, transitions, guards, actions, hierarchical states, parallel regions, and history states.",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        result = response.json()
        return result["choices"][0]["message"]["content"]
    else:
        raise Exception(
            f"OpenRouter API call failed with status {response.status_code}: {response.text}"
        )


# **************** HTML TABLE UTILITY FUNCTIONS ****************


def extract_html_tables(llm_response: str) -> list[Tag]:
    """
    The extract HTML tables function takes in a string representing
    the LLM's response, and extracts all HTML tables in the response.
    A list of BeautifulSoup tags are returned so tables can be further
    processed
    """
    # extract the content within the ```html code blocks using regex
    code_blocks = re.findall(r"```html(.*?)```", llm_response, re.DOTALL)

    tables = []

    # for each HTML code block, parse and extract the tables
    for block in code_blocks:
        # parse the HTML content
        soup = BeautifulSoup(block, "html.parser")

        # find all <table> elements from parsed elements
        table_elements = soup.find_all("table")

        # extract each table's HTML and add to list of tables
        for table in table_elements:
            tables.append(table)

    return tables


def extract_table_using_headers(llm_response: str, headers: list[str]) -> Tag:
    """
    The extract_table_using_headers function extracts all tables with the matching list
    of headers from an LLM response, and returns a BeautifulSoup tag containing the table
    """
    # find all tables in the response
    tables = extract_html_tables(llm_response=llm_response)

    for table in tables:
        current_table_headers = [th.get_text().strip() for th in table.find_all("th")]

        if all(header in current_table_headers for header in headers):
            return table

    return None


def extract_states_events_table(llm_response):
    """
    Extract the states-events table for Linear SMF responses
    """
    states_events_table_headers = ["Current State", "Event", "Next State(s)"]
    states_events_table = extract_table_using_headers(
        llm_response=llm_response, headers=states_events_table_headers
    )
    return states_events_table


def extract_parallel_states_table(llm_response):
    """
    Extracts the parallel states table for Linear SMF responses
    """
    parallel_states_table_headers = ["Parallel State", "Parallel Region", "Substate"]
    parallel_states_table = extract_table_using_headers(
        llm_response=llm_response, headers=parallel_states_table_headers
    )
    return parallel_states_table


def extract_transitions_guards_table(llm_response: str, includeHeader: bool) -> Tag:
    """
    Extracts the table of transitions with headers "From State", "To State", "Event",
    and "Guard" for Linear SMF responses
    """
    transitions_guards_table_headers = ["From State", "To State", "Event", "Guard"]
    transitions_guards_table = extract_table_using_headers(
        llm_response=llm_response, headers=transitions_guards_table_headers
    )
    if not includeHeader and transitions_guards_table:
        first_row = transitions_guards_table.find("th")
        if first_row:
            first_row.decompose()
    return transitions_guards_table


def extract_history_state_table(llm_response: str, includeHeader: bool = False) -> Tag:
    """
    Extracts the table containing history state transitions for History States for
    Linear SMF responses
    """
    history_table_headers = ["From State", "Event", "Guard", "Action"]
    history_table = extract_table_using_headers(
        llm_response=llm_response, headers=history_table_headers
    )
    if history_table and not includeHeader:
        first_row = history_table.find("tr")
        if first_row:
            first_row.decompose()
    return history_table


def extract_hierarchical_state_table(llm_response: str) -> Tag:
    """
    Extracts tables depicting Hierarchical State relationships in
    responses for Event Driven SMF responses
    """
    history_table_headers = ["Superstate", "Substate"]
    history_table = extract_table_using_headers(
        llm_response=llm_response, headers=history_table_headers
    )
    return history_table


def appendTables(table1: Tag, table2: Tag) -> Tag:
    """
    The appendTables function merges the rows of two tables together (assuming
    the two tables have the same headers)
    """
    table1 = BeautifulSoup(str(table1), "html.parser").find_all("table")[0]
    table2 = BeautifulSoup(str(table2), "html.parser").find_all("table")[0]

    for row in table2.find_all("tr"):
        table1.append(row)
    return table1


def addColumn(table: Tag, headerName: str, columnIdx: int, placeholderValue: str):
    """
    The addColumn function adds a new column to a given table at the specified index,
    with the header headerName, and a default value placeholderValue
    """
    soup = BeautifulSoup(str(table), "html.parser")

    # Add a new header for the new column
    if headerName:
        new_header = soup.new_tag("th")
        new_header.string = headerName
        header_row = table.find("tr")
        header_row.insert(columnIdx, new_header)

    # Add new column data to each row
    for row in table.find_all("tr")[1 if headerName else 0 :]:  # Skip the header row
        new_col = soup.new_tag("td")
        new_col.string = placeholderValue
        row.insert(columnIdx, new_col)

    return table


def extractColumn(table, columnIdx: int):
    """
    The extractColumn gets all entries in the column at index
    columnIdx
    """

    table = str_to_Tag(table)
    column_list = []

    # Add new column data to each row
    if table:
        for row in table.find_all("tr")[1:]:  # Skip the header row=
            cols = row.find_all("td")
            column_list.append(cols[columnIdx].get_text())

    return column_list


def extract_transitions_guards_actions_table(llm_response: str) -> Tag:
    """
    Extracts transitions tables with headers "From State", "To State", "Event", "Guard", and
    "Action" for Linear SMF and Event Driven SMF responses
    """
    transitions_guards_table_events_headers = [
        "From State",
        "To State",
        "Event",
        "Guard",
        "Action",
    ]
    transitions_guards_actions_table = extract_table_using_headers(
        llm_response=llm_response, headers=transitions_guards_table_events_headers
    )
    return transitions_guards_actions_table


def str_to_Tag(table: str):
    """
    converts the string of an HTML table into a BeautifulSoup Tag
    """
    tables = BeautifulSoup(str(table), "html.parser").find_all("table")
    return tables[0] if tables else None


# ******************** HTML to JSON (dict) UTILITIES *********************


def format_state_name_for_pytransitions(state_name, hierarchical_states_table):
    """
    given a state name and the table of hierarchical states, format the state's name to be the expected
    format for the transitions for pytransitions. The format is ParentState_ChildState
    """
    child_state_to_parent_state = map_child_state_to_parent_state(
        hierarchical_state_table=hierarchical_states_table
    )
    if (
        child_state_to_parent_state
        and child_state_to_parent_state.get(state_name, None) is not None
    ):
        return f"{child_state_to_parent_state.get(state_name)}_{state_name}"
    else:
        return state_name


def format_state_name_for_pytransitions_arbitrarily_nested(
    state_name, hierarchical_states_table
):
    """
    given a state name and the table of hierarchical states, format the state's name to be the expected
    format for the transitions for pytransitions. The format is ParentState_ChildState
    """
    child_state_to_parent_state = map_state_to_pytransitions_name(
        hierarchical_state_table=hierarchical_states_table
    )
    return child_state_to_parent_state[state_name]


def nest_hierarchical_states(state_to_nest, list_states):
    """The function assumes that the state to nest is a superstate"""
    for state in list_states:
        if isinstance(state, str) and state_to_nest["name"] == state:
            state_idx = list_states.index(state)
            list_states[state_idx] = state_to_nest
            return True
        elif isinstance(state, dict) and "children" in state.keys():
            if nest_hierarchical_states(state_to_nest, state["children"]):
                return True
        elif isinstance(state, dict) and "parallel" in state.keys():
            if nest_hierarchical_states(state_to_nest, state["parallel"]):
                return True

    return False


def gsm_tables_to_dict(
    hierarchical_states_table: Tag,
    transitions_table: Tag,
    parallel_state_table: Tag,
    nesting: bool = True,
):
    """
    Extracts the states, transitions, and parallel regions of a Generated State Machine (GSM) and returns
    them in a list
    """
    hierarchical_states_table = table_remove_spaces(
        str_to_Tag(hierarchical_states_table)
    )
    transitions_table = table_remove_spaces(str_to_Tag(transitions_table))
    parallel_state_table = table_remove_spaces(str_to_Tag(parallel_state_table))
    states = []
    transitions = []
    parallel_states = []

    # Add states to state list
    states += list(
        set(
            extractColumn(hierarchical_states_table, 0)
            + extractColumn(hierarchical_states_table, 1)
            + extractColumn(transitions_table, 0)
            + extractColumn(transitions_table, 1)
            + extractColumn(parallel_state_table, 0)
            + extractColumn(parallel_state_table, 2)
        )
    )

    if transitions_table:
        for row in transitions_table.find_all("tr")[1:]:  # Skip the header row=
            cols = row.find_all("td")
            transition = {
                "trigger": cols[2].get_text(),
                "source": format_state_name_for_pytransitions_arbitrarily_nested(
                    state_name=cols[0].get_text(),
                    hierarchical_states_table=hierarchical_states_table,
                ),
                "dest": format_state_name_for_pytransitions_arbitrarily_nested(
                    state_name=cols[1].get_text(),
                    hierarchical_states_table=hierarchical_states_table,
                ),
            }
            if len(cols) == 5 and cols[4].get_text() != "NONE":
                transition["before"] = cols[4].get_text()
            if len(cols) == 5 and cols[3].get_text() != "NONE":
                transition["conditions"] = cols[3].get_text()

            transitions.append(transition)

    if hierarchical_states_table:
        for row in hierarchical_states_table.find_all("tr")[1:]:  # Skip the header row=
            cols = row.find_all("td")

            try:
                stateIdx = states.index(cols[0].get_text())
            except ValueError:
                stateIdx = [
                    states.index(dic)
                    for dic in states
                    if isinstance(dic, dict) and dic["name"] == cols[0].get_text()
                ][0]

            if not isinstance(states[stateIdx], dict):
                hierarchical_state = {
                    "name": cols[0].get_text(),
                    "children": [cols[1].get_text()],
                }
                states[stateIdx] = hierarchical_state
            else:
                states[stateIdx]["children"].append(cols[1].get_text())

    if parallel_state_table:
        for row in parallel_state_table.find_all("tr")[1:]:  # Skip the header row=
            cols = row.find_all("td")

            try:
                parallel_state_idx = [
                    parallel_states.index(dic)
                    for dic in parallel_states
                    if isinstance(dic, dict) and dic["name"] == cols[0].get_text()
                ][0]
            except IndexError:
                parallel_state_idx = -1

            if parallel_state_idx < 0:
                parallel_state = {
                    "name": cols[0].get_text(),
                    "parallel": [
                        {"name": cols[1].get_text(), "children": cols[2].get_text()}
                    ],
                }
                parallel_states.append(parallel_state)
            else:
                parallel_state = parallel_states[parallel_state_idx]
                # Check if the parallel region is already added
                try:
                    parallel_region_idx = [
                        parallel_state["parallel"].index(dic)
                        for dic in parallel_state["parallel"]
                        if isinstance(dic, dict) and dic["name"] == cols[1].get_text()
                    ][0]
                except IndexError:
                    parallel_region_idx = -1

                if parallel_region_idx < 0:
                    parallel_state["parallel"].append(
                        {"name": cols[1].get_text(), "children": cols[2].get_text()}
                    )
                else:
                    parallel_state["parallel"][parallel_region_idx]["children"].append(
                        cols[2].get_text()
                    )

    # Add the parallel states to the pool of states
    states.extend(parallel_states)

    # States under '-' really don't have a superstate
    non_composite_state = [
        state for state in states if isinstance(state, dict) and state["name"] == "-"
    ]
    if non_composite_state:
        for child in non_composite_state[0]["children"]:
            if child not in states:
                states.append(child)
        states.remove(non_composite_state[0])

    # remove states which are already encompassed by a parent state
    states = [
        state
        for state in states
        if (non_composite_state and state in non_composite_state[0]["children"])
        or isinstance(state, dict)
    ]

    if nesting:
        # Nesting hierarchical states
        for i in range(len(states) - 1, -1, -1):
            if nest_hierarchical_states(states[i], states):
                states.pop(i)

    # Remove all spaces not to confuse mermaid
    # states = list(map(state_remove_spaces, states))
    # transitions = list(map(transitions_remove_spaces, transitions))
    # parallel_states = list(map(regions_remove_spaces, parallel_states))

    return states, transitions, parallel_states


def add_initial_hierarchical_states(
    gsm_states: list, hierarchical_initial_states: dict
):
    """
    the add_initial_hierarchical_states sets the "initial" key of the hierarchical states in the gsm_states
    list to map to the name of the hierarchical state's initial state, as required by pytransitions. note
    that the initial state name does NOT need to be in the format "ParentState_ChildState"
    """

    # iterate over each hierarchical state and its initial state
    for (
        hierarchical_state_name,
        initial_state_name,
    ) in hierarchical_initial_states.items():
        if initial_state_name is not None:
            # locate the hierarchical state in the list of initial states
            for gsm_state in gsm_states:
                # check to see if the current state is the hierarchical state and set the initial state if it is one of the child states
                if (
                    isinstance(gsm_state, dict)
                    and gsm_state.get("name")
                    == hierarchical_state_name.replace(" ", "")
                    and initial_state_name.replace(" ", "") in gsm_state.get("children")
                ):
                    gsm_state["initial"] = initial_state_name.replace(" ", "")
                    break

    return gsm_states


def create_event_based_gsm_diagram(
    hierarchical_states_table: Tag,
    transitions_table: Tag,
    parallel_state_table: Tag,
    initial_state: str,
    hierarchical_initial_states: dict,
    diagram_file_path: str,
):
    gsm_states, gsm_transitions, gsm_parallel_regions = gsm_tables_to_dict(
        hierarchical_states_table=hierarchical_states_table,
        transitions_table=transitions_table,
        parallel_state_table=parallel_state_table,
    )

    # update the states so each hierarchical state contains their initial state
    gsm_states = add_initial_hierarchical_states(
        gsm_states=gsm_states, hierarchical_initial_states=hierarchical_initial_states
    )
    print(f"States: {gsm_states}")
    print(f"Transitions: {gsm_transitions}")
    print(f"Parallel Regions: {gsm_parallel_regions}")

    # Create the state machine
    gsm = SherpaStateMachine(
        states=gsm_states,
        transitions=gsm_transitions,
        initial=format_state_name_for_pytransitions(
            initial_state, hierarchical_states_table=hierarchical_states_table
        ).replace(" ", ""),
        sm_cls=HierarchicalGraphMachine,
    )

    print(gsm.sm.get_graph().draw(None))

    # Generate and render a sequence diagram
    sequence = Graph("Sequence-diagram", gsm.sm.get_graph().draw(None))
    render = md.Mermaid(sequence)
    render.to_png(diagram_file_path)


def get_top_level_state(state, hierarchical_states_table):
    pytransitions_mapping = map_state_to_pytransitions_name(hierarchical_states_table)
    return pytransitions_mapping[state].split("_")[0]


def create_simple_linear_gsm_diagram(
    hierarchical_states_table: Tag,
    transitions_table: Tag,
    parallel_state_table: Tag,
    initial_state: str,
    hierarchical_initial_states: dict,
    diagram_file_path: str,
):
    gsm_states, gsm_transitions, gsm_parallel_regions = gsm_tables_to_dict(
        hierarchical_states_table=hierarchical_states_table,
        transitions_table=transitions_table,
        parallel_state_table=parallel_state_table,
    )

    # update the states so each hierarchical state contains their initial state
    gsm_states = add_initial_hierarchical_states(
        gsm_states=gsm_states, hierarchical_initial_states=hierarchical_initial_states
    )
    print(f"States: {gsm_states}")
    print(f"Transitions: {gsm_transitions}")
    print(f"Parallel Regions: {gsm_parallel_regions}")

    # Create the state machine
    gsm = SherpaStateMachine(
        states=gsm_states,
        transitions=gsm_transitions,
        initial=get_top_level_state(
            initial_state, hierarchical_states_table=hierarchical_states_table
        ).replace(" ", ""),
        sm_cls=HierarchicalGraphMachine,
    )

    print(gsm.sm.get_graph().draw(None))

    # Generate and render a sequence diagram
    sequence = Graph("Sequence-diagram", gsm.sm.get_graph().draw(None))
    render = md.Mermaid(sequence)
    render.to_png(diagram_file_path)


# ********************** FUNCTIONS TO REMOVE SPACES ******************
def table_remove_spaces(table):
    """
    Removes white space from table entries
    """
    if not table:
        return None

    # Find all table cells
    cells = table.find_all("td")

    # Iterate through each cell and remove spaces
    for cell in cells:
        cell.string = cell.get_text().replace(" ", "")

    return table


def state_remove_spaces(state):
    """
    Removes white space from State Table entries
    """

    # the state is a hierarchical state
    if isinstance(state, dict):
        state["name"] = state["name"].replace(" ", "")
        state["children"] = [s.replace(" ", "") for s in state["children"]]
    else:
        # the state is not a hierarchical state
        state = state.replace(" ", "")
    return state


def transitions_remove_spaces(transition):
    """
    Removes white space from state names in a transition dictionary
    """
    transition["source"] = transition["source"].replace(" ", "")
    transition["dest"] = transition["dest"].replace(" ", "")
    return transition


def regions_remove_spaces(region):
    """
    Removes the white space from parallel region and region child states in a region dictionary
    """
    region["name"] = region["name"].replace(" ", "")
    region["regionChildren"] = [s.replace(" ", "") for s in region["regionChildren"]]
    return region


def extract_event_driven_states_table(llm_response: str) -> Tag:
    """
    Extracts the table containing all states of a UML State Machine for Event Driven SMF responses
    """
    event_driven_states_table_headers = ["StateName"]
    event_driven_states_table = extract_table_using_headers(
        llm_response=llm_response, headers=event_driven_states_table_headers
    )
    return event_driven_states_table


def extract_event_driven_events_table(llm_response: str) -> Tag:
    """
    Extracts the table containing all events of a UML State Machine for Event Driven SMF responses
    """
    event_driven_events_table_headers = ["EventName"]
    event_driven_events_table = extract_table_using_headers(
        llm_response=llm_response, headers=event_driven_events_table_headers
    )
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
    header_cells = [th.get_text() for th in html_tables_list[0].find_all("th")]

    # Create a new BeautifulSoup object with an empty table for merging
    merged_table_soup = BeautifulSoup(
        "<table border='1'><tr></tr></table>", "html.parser"
    )
    merged_table = merged_table_soup.find("table")

    # Create header row in the merged table
    header_row = merged_table.find("tr")
    for header in header_cells:
        th = merged_table_soup.new_tag("th")
        th.string = header
        header_row.append(th)

    # Collect all rows from each table and add them to the merged table
    for table_tag in html_tables_list:
        rows = table_tag.find_all("tr")[1:]  # Skip the header row

        for row in rows:
            new_row = merged_table_soup.new_tag("tr")
            for cell in row.find_all("td"):
                new_cell = merged_table_soup.new_tag("td")
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
    from_state_transitions_table = BeautifulSoup(
        "<table border='1'></table>", "html.parser"
    )
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
    hierarchical_state_table = str_to_Tag(hierarchical_state_table)

    child_to_parent_dict = {}

    # extract all rows except for header
    if hierarchical_state_table:
        rows = hierarchical_state_table.find_all("tr")[1:]

        for row in rows:
            cells = row.find_all("td")
            parent_state = cells[0].get_text(strip=True)
            child_state = cells[1].get_text(strip=True)

            # only create mappings for states that actually have a parent in the hierarchy
            if parent_state != "-":
                child_to_parent_dict[child_state] = parent_state

    return child_to_parent_dict


def map_state_to_pytransitions_name(hierarchical_state_table):
    state_to_pytransitions_name = {}

    child_to_parent_dict = map_child_state_to_parent_state(hierarchical_state_table)
    children_set = set(list(child_to_parent_dict.keys()))
    parents_set = set(list(child_to_parent_dict.values()))
    top_level_parents = list(parents_set - children_set)

    for child in child_to_parent_dict.keys():
        # Form the child pytransition name
        parent_name = child_to_parent_dict[child]
        parent_pytransitions_name = (
            state_to_pytransitions_name[parent_name]
            if parent_name in state_to_pytransitions_name.keys()
            else parent_name
        )
        child_pytransitions_name = "_".join([parent_pytransitions_name, child])

        # Rectify any name of children of child already in state_to_pytransitions_name
        for state in state_to_pytransitions_name.keys():
            if state_to_pytransitions_name[state].split("_")[0] == child:
                state_to_pytransitions_name[state] = "_".join(
                    child_pytransitions_name, state_to_pytransitions_name[state]
                )

        # Finally update the child name itself in state_to_pytransitions_name
        state_to_pytransitions_name[child] = child_pytransitions_name

    # Add a mapping for the top level parents
    for state in top_level_parents:
        state_to_pytransitions_name[state] = state

    return state_to_pytransitions_name


def refactor_transition_table_with_parent_states(
    transitions_table, hierarchical_state_table
):
    """
    Replaces the "From State" and "To State" columns with states named in the format ParentState.ChildState
    """

    # map each child state to its parent, if it has one
    child_to_parent_dict = map_child_state_to_parent_state(
        hierarchical_state_table=hierarchical_state_table
    )

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
    soup = BeautifulSoup(html_table, "html.parser")
    table = soup.find("table")

    headers = []
    header_row = table.find("tr")
    if header_row:
        for th in header_row.find_all("th"):
            header = th.get_text(strip=True)
            headers.append(header)
    else:
        first_row = table.find("tr")
        num_columns = len(first_row.find_all(["th", "td"]))
        headers = ["Column {}".format(i + 1) for i in range(num_columns)]

    data = []

    for row in table.find_all("tr")[1:]:
        cols = row.find_all("td")
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
        superstate = entry["Superstate"]
        substate = entry["Substate"]
        if superstate != "-":
            if superstate not in hierarchy:
                hierarchy[superstate] = []
            hierarchy[superstate].append(substate)

    return hierarchy


def umpleCodeSearch(llm_response: str, generated_umple_code_path: str, writeFile=True):
    """Function that extracts umple code from an LLM response
    params:
    llm_response is the string response from the LLM
    generated_umple_code_path is the path of the file in which to write the extracted umple code. The file path must have the extension ".ump"

    raises:
    Exception if no umple code is found in the extracted code"""
    generated_umple_code_search = re.search(
        r"<umple_code_solution>(.*?)</umple_code_solution>", llm_response, re.DOTALL
    )

    if generated_umple_code_search:
        generated_umple_code = generated_umple_code_search.group(1)
    else:
        raise Exception

    if writeFile:
        # Create a file to store generated code
        with open(generated_umple_code_path, "w") as file:
            file.write(generated_umple_code)

    return generated_umple_code


def mermaidCodeSearch(
    llm_response: str, generated_mermaid_code_path: str, writeFile=True
):
    """Function that extracts mermaid code from an LLM response
    params:
    llm_response is the string response from the LLM
    generated_mermaid_code_path is the path of the file in which to write the extracted mermaid code. The file path must have the extension ".mmd"

    raises:
    Exception if no mermaid code is found in the extracted code"""

    # Try to find code wrapped in XML-style tags first
    generated_mermaid_code_search = re.search(
        r"<mermaid_code_solution>\s*(.*?)\s*</mermaid_code_solution>",
        llm_response,
        re.DOTALL,
    )

    if generated_mermaid_code_search:
        generated_mermaid_code = generated_mermaid_code_search.group(1).strip()
    else:
        # Try to find code in markdown code blocks with mermaid language tag
        mermaid_block_search = re.search(
            r"```mermaid\s*(.*?)```", llm_response, re.DOTALL
        )
        if mermaid_block_search:
            generated_mermaid_code = mermaid_block_search.group(1).strip()
        else:
            # Try to find stateDiagram-v2 directly (last resort)
            # Look for stateDiagram-v2 and capture everything after it
            if "stateDiagram-v2" in llm_response:
                start_idx = llm_response.find("stateDiagram-v2")
                generated_mermaid_code = llm_response[start_idx:]
            else:
                raise Exception("No mermaid code found in LLM response")

    # Defensive sanitization: remove common copy/paste artifacts that break the JS parser
    # - remove markdown fences and mermaid code fences
    generated_mermaid_code = re.sub(
        r"```(?:mermaid)?\s*", "", generated_mermaid_code, flags=re.IGNORECASE
    )
    # - remove Python/JS triple-quote artifacts that sometimes are included in LLM outputs
    generated_mermaid_code = generated_mermaid_code.replace('"""', "").replace(
        "'''", ""
    )
    # - strip surrounding backticks, quotes and whitespace
    generated_mermaid_code = generated_mermaid_code.strip("` \t\r\n'\"")
    # - remove any trailing unmatched triple quotes
    generated_mermaid_code = re.sub(r'("{3,}|\'{3,})\s*$', "", generated_mermaid_code)

    # ALWAYS clean up - find stateDiagram-v2 and take ONLY from that point forward
    if "stateDiagram-v2" in generated_mermaid_code:
        start_idx = generated_mermaid_code.find("stateDiagram-v2")
        generated_mermaid_code = generated_mermaid_code[start_idx:]

    # Remove any trailing closing tags or extra text after the diagram
    # Find the last closing brace at the root level (end of state machine)
    lines = generated_mermaid_code.split("\n")
    # Keep lines until we find a line that's just a closing tag or starts with <
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        if (
            stripped.startswith("</")
            or stripped.startswith("<mermaid")
            or stripped == "```"
            or stripped.startswith('"""')
            or stripped.startswith("'''")
            or stripped.endswith('"""')
            or stripped.endswith("'''")
        ):
            break
        cleaned_lines.append(line)

    generated_mermaid_code = "\n".join(cleaned_lines).strip()

    if writeFile:
        # Create a file to store generated code
        with open(generated_mermaid_code_path, "w") as file:
            file.write(generated_mermaid_code)

    return generated_mermaid_code


def setup_file_paths(
    base_dir: str,
    file_type: str = "single_prompt",
    system_name: str = None,
    model_name: str = None,
) -> dict:
    """
    Setup file paths for logs, Umple code, Mermaid code, and diagrams
    Args:
        base_dir: Base directory path
        file_type: Type of file (default: "single_prompt")
        system_name: Optional name of the system being generated (e.g., "Printer", "Custom")
        model_name: Optional name of the model used (e.g., "claude-4-5-sonnet", "gpt-4o")
    Returns:
        dict: Dictionary containing all necessary file paths
    """

    # For single_prompt, organize files in timestamped folders with optional system name
    if file_type == "single_prompt":
        # Create date and time parts separately
        date_folder = time.strftime("%Y_%m_%d")  # e.g., 2026_01_30
        time_folder = time.strftime("%H_%M_%S")  # e.g., 16_38_49

        # Create single output directory with structure: date/model_name/system_name/time
        # Sanitize model_name to be filesystem-safe
        if model_name:
            safe_model_name = model_name.replace("/", "-").replace(":", "-")
        else:
            safe_model_name = "unknown_model"

        if system_name:
            # Sanitize system_name to be filesystem-safe
            safe_system_name = "".join(
                c if c.isalnum() or c in (" ", "-", "_") else "_" for c in system_name
            )
            safe_system_name = safe_system_name.strip().replace(" ", "_")
            output_base_dir = os.path.join(
                base_dir,
                "resources",
                f"{file_type}_outputs",
                date_folder,
                safe_model_name,
                safe_system_name,
                time_folder,
            )
        else:
            output_base_dir = os.path.join(
                base_dir,
                "resources",
                f"{file_type}_outputs",
                date_folder,
                safe_model_name,
                time_folder,
            )
        os.makedirs(output_base_dir, exist_ok=True)

        # Generate file names (simpler since they're in a timestamped folder)
        file_prefix = f"output_{file_type}"
        log_file_name = f"{file_prefix}.txt"

        return {
            "log_base_dir": output_base_dir,
            "log_file_path": os.path.join(output_base_dir, log_file_name),
            "generated_umple_code_path": os.path.join(
                output_base_dir, f"{file_prefix}.ump"
            ),
            "generated_mermaid_code_path": os.path.join(
                output_base_dir, f"{file_prefix}.mmd"
            ),
            "umple_jar_path": os.path.join(base_dir, "resources", "umple.jar"),
            "diagram_base_dir": output_base_dir,
            "diagram_file_path": os.path.join(output_base_dir, file_prefix),
        }
    else:
        # Keep existing behavior for other file types (event_driven, simple_linear)
        # Setup directories
        log_base_dir = os.path.join(base_dir, "resources", f"{file_type}_log")
        diagram_base_dir = os.path.join(base_dir, "resources", f"{file_type}_diagrams")

        # Create directories
        os.makedirs(log_base_dir, exist_ok=True)
        os.makedirs(diagram_base_dir, exist_ok=True)

        # Generate file names
        file_prefix = f'output_{file_type}_{time.strftime("%Y_%m_%d_%H_%M_%S")}'
        log_file_name = f"{file_prefix}.txt"

        return {
            "log_base_dir": log_base_dir,
            "log_file_path": os.path.join(log_base_dir, log_file_name),
            "generated_umple_code_path": os.path.join(
                log_base_dir, f"{file_prefix}.ump"
            ),
            "generated_mermaid_code_path": os.path.join(
                log_base_dir, f"{file_prefix}.mmd"
            ),
            "umple_jar_path": os.path.join(base_dir, "resources", "umple.jar"),
            "diagram_base_dir": diagram_base_dir,
            "diagram_file_path": os.path.join(diagram_base_dir, file_prefix),
        }


def umpleCodeProcessing(
    umple_jar_path: str, generated_umple_code_path: str, log_base_dir: str
):
    """Function to compile umple code and generate graphviz file
    params:
    umple_jar_path is the path to the jar executable that compiles umple code
    generated_umple_code_path is the path the umple file containing the code to compile
    log_base_dir is the directory under which to output the compiled code (the file containing the compiled code is named the same as the umple file with a different extension)

    returns:
    the path of the generated graphviz file

    raises:
    subprocess.CalledProcessError if the umple code is contains errors"""
    subprocess.run(
        [
            "java",
            "-jar",
            umple_jar_path,
            generated_umple_code_path,
            "-g",
            "GvStateDiagram",
            "--path",
            log_base_dir,
        ],
        capture_output=True,
        check=True,
        text=True,
    )

    return os.path.join(
        log_base_dir,
        f"{os.path.splitext(os.path.basename(generated_umple_code_path))[0]}.gv",
    )


def graphVizGeneration(generated_umple_gv_path, diagram_file_path: str):
    """Function that interprets GraphViz file (.gv) to produce GraphViz diagram image
    params:
    generated_umple_gv_path is the file that contains the graphviz code (it is returned by the umpleCodeProcessing function)
    diagram_file_path is the path where to output the .png diagram
    """
    with open(generated_umple_gv_path, "r") as file:
        dot_code = file.read()

    # Render the DOT file using Graphviz
    graph = graphviz.Source(dot_code)
    graph.render(diagram_file_path, format="png")


# NOTE: parse_mermaid_to_sherpa_format is DEAD CODE NOW.
# The single prompt flow uses parse_mermaid_with_library from mermaid_to_sherpa_parser.py instead.
# Commented out for now, the other formnats technically still rely on this.
#
# def parse_mermaid_to_sherpa_format(mermaid_code: str):
#     """
#     Parse Mermaid stateDiagram-v2 syntax and extract states, transitions, and hierarchical relationships
#     Returns: (states_list, transitions_list, hierarchical_dict, initial_state, parallel_regions)
#     """
#     lines = mermaid_code.strip().split('\n')
#     states = set()
#     transitions = []
#     hierarchical_states = {}  # parent -> [children]
#     parallel_regions = []
#     initial_state = None
#     current_parent_stack = []  # Track nested hierarchy
#
#     for line in lines:
#         line = line.strip()
#
#         # Skip empty lines, comments, and the header
#         if not line or line.startswith('stateDiagram') or line.startswith('note'):
#             continue
#
#         # Handle state block opening: "state StateName {"
#         if re.match(r'state\s+(\w+)\s*\{', line):
#             state_name_match = re.search(r'state\s+(\w+)\s*\{', line)
#             if state_name_match:
#                 parent_state = state_name_match.group(1)
#                 states.add(parent_state)
#                 current_parent_stack.append(parent_state)
#                 if parent_state not in hierarchical_states:
#                     hierarchical_states[parent_state] = []
#             continue
#
#         # Handle closing braces (end of state block)
#         if line == '}':
#             if current_parent_stack:
#                 current_parent_stack.pop()
#             continue
#
#         # Handle parallel region separator
#         if line == '--':
#             continue
#
#         # Handle initial state: "[*] --> StateName"
#         initial_match = re.match(r'\[\*\]\s*-->\s*(\w+)', line)
#         if initial_match:
#             target_state = initial_match.group(1)
#             states.add(target_state)
#
#             # If we're inside a parent state, this is the child's initial state
#             if current_parent_stack:
#                 parent = current_parent_stack[-1]
#                 if parent not in hierarchical_states:
#                     hierarchical_states[parent] = []
#                 if target_state not in hierarchical_states[parent]:
#                     hierarchical_states[parent].append(target_state)
#             else:
#                 # Top-level initial state
#                 initial_state = target_state
#             continue
#
#         # Handle transitions: "StateA --> StateB : event [guard] / action"
#         transition_match = re.match(r'(\w+)\s*-->\s*(\w+)(?:\s*:\s*(.+))?', line)
#         if transition_match:
#             from_state = transition_match.group(1)
#             to_state = transition_match.group(2)
#             label = transition_match.group(3) if transition_match.group(3) else None
#
#             states.add(from_state)
#             states.add(to_state)
#
#             # Add to hierarchical states if inside a parent
#             if current_parent_stack:
#                 parent = current_parent_stack[-1]
#                 if parent not in hierarchical_states:
#                     hierarchical_states[parent] = []
#                 for state in [from_state, to_state]:
#                     if state not in hierarchical_states[parent]:
#                         hierarchical_states[parent].append(state)
#
#             # Parse transition label for event, guard, and action
#             trigger = None
#             guard = None
#             action = None
#
#             if label:
#                 # Extract action: / {action}
#                 action_match = re.search(r'/\s*\{(.+?)\}', label)
#                 if action_match:
#                     action = action_match.group(1)
#                     label = re.sub(r'/\s*\{.+?\}', '', label).strip()
#
#                 # Extract guard: [condition]
#                 guard_match = re.search(r'\[(.+?)\]', label)
#                 if guard_match:
#                     guard = guard_match.group(1)
#                     label = re.sub(r'\[.+?\]', '', label).strip()
#
#                 # What remains is the trigger/event
#                 trigger = label.strip() if label.strip() else None
#
#             # Format state names with parent prefix for pytransitions
#             if current_parent_stack:
#                 from_formatted = '_'.join(current_parent_stack + [from_state])
#                 to_formatted = '_'.join(current_parent_stack + [to_state])
#             else:
#                 from_formatted = from_state
#                 to_formatted = to_state
#
#             transition = {
#                 'trigger': trigger if trigger else 'auto',
#                 'source': from_formatted,
#                 'dest': to_formatted
#             }
#
#             if guard:
#                 transition['conditions'] = guard
#             if action:
#                 transition['before'] = action
#
#             transitions.append(transition)
#
#     # Convert hierarchical_states to the format needed for Sherpa
#     states_list = []
#     for state in states:
#         if state in hierarchical_states:
#             # This is a composite state
#             states_list.append({
#                 'name': state,
#                 'children': hierarchical_states[state]
#             })
#         elif not any(state in children for children in hierarchical_states.values()):
#             # This is a simple state (not a child of any parent)
#             states_list.append(state)
#
#     return states_list, transitions, hierarchical_states, initial_state, parallel_regions


def create_single_prompt_gsm_diagram_with_sherpa(
    mermaid_code: str, diagram_file_path: str
):
    """
    Create a state machine diagram from Mermaid code using Sherpa

    params:
    mermaid_code: The Mermaid stateDiagram-v2 code as a string
    diagram_file_path: Path where to save the PNG diagram
    """
    # Lazy import to avoid pythonmonkey segfault in async context
    # Use absolute import to avoid KeyError with module caching
    try:
        from resources.mermaid_to_sherpa_parser import parse_mermaid_with_library
    except KeyError:
        # Fallback to direct import if relative import fails
        import sys
        import os

        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        from mermaid_to_sherpa_parser import parse_mermaid_with_library

    # Parse Mermaid code using mermaid-parser-py library
    (
        states_list,
        transitions_list,
        hierarchical_dict,
        initial_state,
        parallel_regions,
        state_annotations,
        root_initial_state,
        nested_initial_states,
    ) = parse_mermaid_with_library(mermaid_code)

    print("\nParsed Mermaid Diagram:")
    print("\n")
    print(f"Parsed States: {states_list}")
    print("\n")
    print(f"Parsed Transitions: {transitions_list}")
    print("\n")
    print(f"Initial State: {initial_state}")
    print("\n")
    print(f"State Annotations: {state_annotations}")

    if not initial_state:
        print("Warning: No initial state found, using first state")
        if states_list:
            initial_state = (
                states_list[0]
                if isinstance(states_list[0], str)
                else states_list[0]["name"]
            )
        else:
            raise ValueError("No states found in Mermaid diagram")

    # Create the Sherpa state machine
    try:
        gsm = SherpaStateMachine(
            states=states_list,
            transitions=transitions_list,
            initial=initial_state,
            sm_cls=HierarchicalGraphMachine,
        )

        # Override the default 'active' styling from transitions' diagrams
        # (which uses a colored fill like 'darksalmon') so active states
        # don't appear with the coral/darksalmon fill. Use the machine's
        # default node/graph styles instead.
        try:
            node_defaults = (
                gsm.sm.style_attributes.get("node", {}).get("default", {}).copy()
            )
            graph_defaults = (
                gsm.sm.style_attributes.get("graph", {}).get("default", {}).copy()
            )
            gsm.sm.style_attributes.setdefault("node", {})["active"] = node_defaults
            gsm.sm.style_attributes.setdefault("graph", {})["active"] = graph_defaults
        except Exception:
            # Non-fatal: if attributes aren't present, continue with defaults
            pass

        # Ensure the diagram path has .png extension
        if not diagram_file_path.endswith(".png"):
            png_file_path = f"{diagram_file_path}.png"
        else:
            png_file_path = diagram_file_path

        # Get the graph and manually add initial state markers ([*])
        # These are visual-only markers and must be placed at the correct hierarchical level
        graph = gsm.sm.get_graph()

        # Manually add initial state markers to the Graphviz graph
        # Strategy: Insert point nodes and edges at the correct hierarchical levels
        try:
            import re

            new_body = []

            # Track which subgraphs (composite states) we're inside
            current_subgraphs = []  # Stack of (subgraph_name, indent_level)

            # Process each line and inject initial markers at the right places
            i = 0
            while i < len(graph.body):
                line = graph.body[i]

                # Track subgraph entries
                if "subgraph" in line:
                    # Extract the subgraph name (e.g., cluster_On)
                    match = re.search(r"subgraph\s+(\S+)", line)
                    if match:
                        subgraph_name = match.group(1)
                        indent_match = re.match(r"(\s*)", line)
                        indent_level = len(indent_match.group(1)) if indent_match else 0
                        current_subgraphs.append((subgraph_name, indent_level))

                        # Check if this subgraph corresponds to a composite state with an initial state
                        # Subgraph names are like "cluster_On" or "cluster_On_Busy"
                        # We need to match against the state names in nested_initial_states
                        # nested_initial_states has keys like "On", "On_Busy", etc.
                        state_name = subgraph_name.replace("cluster_", "")

                        new_body.append(line)

                        # If this composite state has an initial state, add the marker
                        if state_name in nested_initial_states:
                            child_initial = nested_initial_states[state_name]
                            # Add the initial marker node and edge
                            marker_name = f"{state_name}_initial"
                            child_scoped = f"{state_name}_{child_initial}"

                            # Calculate proper indentation (one level deeper than subgraph)
                            indent = "\t" * (len(current_subgraphs) + 1)

                            # Add point node definition
                            new_body.append(
                                f'{indent}"{marker_name}" [fillcolor=black color=black height=0.15 label="" shape=point width=0.15]'
                            )
                            # Add edge from marker to initial child state
                            new_body.append(
                                f'{indent}"{marker_name}" -> "{child_scoped}"'
                            )

                        i += 1
                        continue

                # Track subgraph exits
                if line.strip() == "}":
                    if current_subgraphs:
                        # Check indent level to see if we're exiting a subgraph
                        indent_match = re.match(r"(\s*)", line)
                        current_indent = (
                            len(indent_match.group(1)) if indent_match else 0
                        )

                        # Pop subgraphs that we're exiting
                        while (
                            current_subgraphs
                            and current_subgraphs[-1][1] >= current_indent
                        ):
                            current_subgraphs.pop()

                # Keep the line
                new_body.append(line)
                i += 1

            # Add root-level initial marker if needed
            # Root initial marker should be at the top level (not inside any subgraph)
            if root_initial_state:
                # Find where to insert the root initial marker
                # It should be after the graph attributes but before state definitions
                insert_index = 0
                for idx, line in enumerate(new_body):
                    if (
                        "digraph" in line
                        or "graph [" in line
                        or "node [" in line
                        or "edge [" in line
                    ):
                        insert_index = idx + 1
                    elif "subgraph" in line:
                        break

                # Insert root initial marker at top level
                root_marker = "_initial"
                new_body.insert(
                    insert_index,
                    f'\t"{root_marker}" [fillcolor=black color=black height=0.15 label="" shape=point width=0.15]',
                )
                new_body.insert(
                    insert_index + 1, f'\t"{root_marker}" -> "{root_initial_state}"'
                )

            # Replace the graph body
            graph.body = new_body

        except Exception as e:
            # Non-fatal: if this fails, continue with default rendering
            print(f"Warning: Could not add initial state markers: {e}")
            import traceback

            traceback.print_exc()

        if state_annotations:
            # Format annotations as a left-aligned label at the bottom of the diagram
            annotation_text = (
                "\\l".join(state_annotations) + "\\l"
            )  # \l = left-align in graphviz
            graph.graph_attr["label"] = annotation_text
            graph.graph_attr["labelloc"] = "b"  # bottom
            graph.graph_attr["labeljust"] = "l"  # left-justify
            graph.graph_attr["fontsize"] = "10"

        # Generate and render the diagram directly to PNG using graphviz
        graph.draw(png_file_path, prog="dot", format="png")

        print(f"Sherpa diagram saved to: {png_file_path}")
        return True

    except Exception as e:
        print(f"Error creating Sherpa state machine: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


def mermaidDiagramGeneration(mermaid_code_path: str, diagram_file_path: str):
    """Function that renders a Mermaid diagram to PNG
    params:
    mermaid_code_path is the path to the file containing the mermaid code (.mmd file)
    diagram_file_path is the path where to output the .png diagram (without .png extension)
    """
    with open(mermaid_code_path, "r") as file:
        mermaid_code = file.read()

    # Ensure the diagram path has .png extension
    if not diagram_file_path.endswith(".png"):
        png_file_path = f"{diagram_file_path}.png"
    else:
        png_file_path = diagram_file_path

    # Create a mermaid graph and render to PNG
    try:
        sequence = Graph("State-Machine-Diagram", mermaid_code)
        render = md.Mermaid(sequence)
        render.to_png(png_file_path)
        print(f"Mermaid diagram saved to: {png_file_path}")
    except Exception as e:
        print(f"Error rendering Mermaid diagram: {str(e)}")
        raise


def process_umple_attempt(i: int, prompt: str, paths: dict) -> str:
    """
    Process a single attempt at generating and processing Umple code
    Args:
        i: Attempt number
        prompt: LLM prompt
        paths: Dictionary containing file paths
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        answer = call_llm(prompt)

        # Extract Umple code
        try:
            generated_umple_code = umpleCodeSearch(
                answer, paths["generated_umple_code_path"]
            )
        except Exception as e:
            error = f"Attempt {i} at extracting umple code failed\n\n"
            with open(paths["log_file_path"], "a") as file:
                file.write(error)
            print(error)
            return "False"

        print(f"Attempt {i} at extracting umple code successful\nGenerated umple code:")
        print(generated_umple_code)

        # Log generated code
        with open(paths["log_file_path"], "a") as file:
            file.write(generated_umple_code)

        # Process Umple code
        try:
            generated_umple_gv_path = umpleCodeProcessing(
                paths["umple_jar_path"],
                paths["generated_umple_code_path"],
                paths["log_base_dir"],
            )
        except subprocess.CalledProcessError as e:
            error = f"Attempt {i} at processing umple code failed\n\n"
            with open(paths["log_file_path"], "a") as file:
                file.write(error)
                file.write(f"{e.stderr}\n\n")
            print(error)
            print(f"{e.stderr}\n\n")
            return "False"

        print(f"Attempt {i} at processing umple code successful")

        # Generate GraphViz diagram
        graphVizGeneration(generated_umple_gv_path, paths["diagram_file_path"])
        return generated_umple_code

    except Exception as e:
        print(f"Unexpected error in attempt {i}: {str(e)}")
        return "False"


if __name__ == "__main__":
    prompt = (
        "Hi, I need help answering a question about states machines. What are events?"
    )
    model = "google:gemini-1.5-pro-001"
    llm_response = call_llm(prompt)
    print(llm_response)
