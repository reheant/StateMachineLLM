from resources.state_machine_descriptions import *

n_shot_examples = {
    "printer_winter_2017": {
        "system_description": printer_winter_2017,

        "system_name": "Printer",

        "states_table": """```html<table border="1">
        <tr><th>StateName</th></tr>
        <tr><th>Off</th></tr>
        <tr><td>On</td></tr>
        <tr><td>Idle</td></tr>
        <tr><td>Ready</td></tr>
        <tr><td>Scan&Email</td></tr>
        <tr><td>Print</td></tr>
        <tr><td>Suspended</td></tr>
        <tr><td>Busy</td></tr>
        </table>```""",

        "initial_state": "Off",

        "events_table": """```html<table border="1">
        <tr><th>on</th></tr>
        <tr><td>off</td></tr>
        <tr><td>login(cardID)</td></tr>
        <tr><td>logoff</td></tr>
        <tr><td>start</td></tr>
        <tr><td>scan</td></tr>
        <tr><td>cancel</td></tr>
        <tr><td>jam</td></tr>
        <tr><td>resume</td></tr>
        <tr><td>outOfPaper</td></tr>
        <tr><td>print</td></tr>
        <tr><td>done</td></tr>
        <tr><td>stop</td></tr>
        </table>```""",

        "state_inspected": "Ready",

        "associated_events": "logoff, start, scan, print",

        "event_inspected": "start",

        "create_transitions": """```html<table border="1">
        <tr><th>FromState</th><th>ToState</th><th>Event</th><th>Guard</th><th>Action</th></tr>
        <tr><td rowspan="3">Ready</td><td>Ready</td><td>start</td><td>action=="scan"&&!originalLoaded()</td><td>NONE</td></tr>
        <tr><td rowspan="3">Ready</td><td>Ready</td><td>start</td><td>action=="print"&&!documentInQueue()</td><td>NONE</td></tr>
        <tr><td rowspan="3">Ready</td><td>Scan&Email</td><td>start</td><td>action=="scan"&&originalLoaded()</td><td>NONE</td></tr>
        <tr><td rowspan="3">Ready</td><td>Print</td><td>start</td><td>action=="print"&&documentInQueue()</td><td>NONE</td></tr>
        </table>```""",

        "hierarchical_table":"""```html<table border="1">
        <tr><th>Superstate</th><th>Substate</th></tr>
        <tr><td>-</td><td>Off</td></tr>
        <tr><td>-</td><td>On</td></tr>
        <tr><td>On</td><td>Idle</td></tr>
        <tr><td>On</td><td>Ready</td></tr>
        <tr><td>On</td><td>Busy</td></tr>
        <tr><td>On</td><td>Suspended</td></tr>
        <tr><td>Busy</td><td>ScanAndEmail</td></tr>
        <tr><td>Busy</td><td>Print</td></tr></table>```""",

        "transitions_table": """```html<table border="1">
        <tr><th>FromState</th><th>ToState</th><th>Event</th><th>Guard</th><th>Action</th></tr>
        <tr><td>Off</td><td>On</td><td>on</td><td>NONE</td><td>NONE</td></tr>
        <tr><td>On</td><td>Off</td><td>off</td><td>NONE</td><td>NONE</td></tr>
        <tr><td>Idle</td><td>Idle</td><td>login(cardID)</td><td>!idAuthorized(cardID)</td><td>NONE</td></tr>
        <tr><td>Idle</td><td>Ready</td><td>login(cardID)</td><td>idAuthorized(cardID)</td><td>action="none";</td></tr>
        <tr><td>Ready</td><td>Idle</td><td>logoff</td><td>NONE</td><td>NONE</td></tr>
        <tr><td>Ready</td><td>Ready</td><td>start</td><td>action=="scan"&&!originalLoaded()</td><td>NONE</td></tr>
        <tr><td>Ready</td><td>Ready</td><td>start</td><td>action=="print"&&!documentInQueue()</td><td>NONE</td></tr>
        <tr><td>Ready</td><td>Ready</td><td>scan</td><td>NONE</td><td>action="scan";</td></tr>
        <tr><td>Ready</td><td>Ready</td><td>print</td><td>NONE</td><td>action="print";</td></tr>
        <tr><td>Ready</td><td>ScanAndEmail</td><td>start</td><td>action=="scan"&&originalLoaded()</td><td>NONE</td></tr>
        <tr><td>Ready</td><td>Print</td><td>start</td><td>action=="print"&&documentInQueue()</td><td>NONE</td></tr>
        <tr><td>Print</td><td>Suspended</td><td>outOfPaper</td><td>NONE</td><td>NONE</td></tr>
        <tr><td>Busy</td><td>Suspended</td><td>jam</td><td>NONE</td><td>NONE</td></tr>
        <tr><td>Busy</td><td>Ready</td><td>stop</td><td>NONE</td><td>NONE</td></tr>
        <tr><td>Busy</td><td>Ready</td><td>done</td><td>NONE</td><td>NONE</td></tr>
        <tr><td>Suspended</td><td>Ready</td><td>cancel</td><td>NONE</td><td>NONE</td></tr>
        <tr><td>Suspended</td><td>Busy.H</td><td>resume</td><td>NONE</td><td>NONE</td></tr></table>```""",
        
        "superstate_inspected": "On",

        "substates_inspected": "['Idle', 'Ready', 'Busy', 'Suspended']",

        "superstate_initial_state": "Idle",

        "superstate_inspected_for_history_state": "Busy",

        "substates_inspected_for_history_state": "['Scan&Email', 'Print']",

        "history_state_table": """```html<table border="1"> 
        <tr><th>FromState</th><th>Event</th><th>Guard</th><th>Action</th></tr>
        <tr><td>Suspended</td><td>resume</td><td>NONE</td><td>NONE</td></tr>
        </table>```""",
    },
    "spa_manager_winter_2018": {
        "system_description": spa_manager_winter_2018,
        "system_name": "SpaManager",
        "states_table": """<table border="1">
        <tr><th>StateName</th></tr>
        <tr><th>JacuzziOff</th></tr>
        <tr><td>JacuzziOn</td></tr>
        <tr><td>JacuzziLevel1</td></tr>
        <tr><td>JacuzziLevel2</td></tr>
        <tr><td>JacuzziLevel3</td></tr>
        <tr><td>JacuzziPaused</td></tr>
        <tr><td>SaunaOff</td></tr>
        <tr><td>SaunaOn</td></tr>
        <tr><td>SaunaOff</td></tr>
        <tr><td>HeaterHeating</td></tr>
        <tr><td>HeaterIdle</td></tr>
        <tr><td>FanOff</td></tr>
        <tr><td>FanOn</td></tr>
        <tr><td>WaterIdle</td></tr>
        </table>"""
        }
}

def get_n_shot_examples(example_names, tables):
    result = ""
    for i, example in enumerate(example_names):
        if example in n_shot_examples:
            result += f"Example {i+1}:\n"
            for table in tables:
                result += f"\n{table}:\n<{table}>{n_shot_examples[example][table]}</{table}>\n"
            result += "\n"
    return result.strip()
