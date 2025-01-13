from resources.state_machine_descriptions import printer_winter_2017, dishwasher_winter_2019

n_shot_examples = {
    "dishwasher_winter_2019": {
        "system_description": dishwasher_winter_2019,
        "system_name": "Dishwasher",
        "states_table": """```html<table border="1">
        <tr><th>StateName</th></tr>
        <tr><td>Open</td></tr>
        <tr><td>Closed</td></tr>
        <tr><td>Locked</td></tr>
        <tr><td>Idle</td></tr>
        <tr><td>Intake</td></tr>
        <tr><td>Washing</td></tr>
        <tr><td>Drain</td></tr>
        <tr><td>Drying</td></tr>
        <tr><td>Suspended</td></tr>
        </table>```""",

        "initial_state": "Idle",

        "events_table": """```html<table border="1">
        <tr><th>EventName</th></tr>
        <tr><td>Turn dishwasher on</td></tr>
        <tr><td>Toggle dishwasher program</td></tr>
        <tr><td>Toggle dishwasher drying runtime</td></tr>
        <tr><td>Start the Dishwasher</td></tr>
        <tr><td>Dishwasher is washing</td></tr>
        <tr><td>Dishwasher Waiting</td></tr>
        <tr><td>Dishwasher Draining</td></tr>
        <tr><td>Dishwasher Paused</td></tr>
        <tr><td>Dishwasher Drying</td></tr>
        <tr><td>Extend Dishwasher Drying Time</td></tr>
        <tr><td>Stop Dishwasher Drying</td></tr>
        <tr><td>Dishwasher resumed using the same settings</td></tr>
        <tr><td>Open Dishwasher Door</td></tr>
        <tr><td>Close Dishwasher Door</td></tr>
        <tr><td>Lock the dishwasher Door</td></tr>
        <tr><td>Unlock the dishwasher Door</td></tr>
        </table>```""",

        "state_inspected": "Idle",

        "associated_events": """
        Toggle dishwasher program,
        Toggle dishwasher drying runtime,
        Start the Dishwasher,
        Close Dishwasher Door, 
        Lock the dishwasher Door,
        Dishwasher Waiting, """,

        "event_inspected": "Turn dishwasher on",

        "create_transitions": """```html<table border="1">
        <tr><th>From State</th><th>To State</th><th>Event</th><th>Guard</th><th>Action</th></tr>
        <tr><td>Idle</td><td>Idle</td><td>Toggle dishwasher program</td><td>[Program number >= 1]</td><td>Diswasher repetitions = Program Number</td></tr>
        <tr><td>Idle</td><td>Idle</td><td>Toggle drying time</td><td>NONE</td><td>if drying time equal to 20 then set it to 40 otherwise set it to 20</td></tr>
        <tr><td>Idle</td><td>Idle</td><td>Toggle dishwasher drying time & Diswasher Waiting</td><td>NONE</td><td>if drying time equal to 20 then set it to 40 otherwise set it to 20</td></tr>
        <tr><td>Idle</td><td>Intake</td><td>Start the diswasher</td><td>[Dishwasher door is closed]</td><td>Lock the dishwasher door and set the counter = 1</td></tr>
        <tr><td>Idle</td><td>Washing</td><td>Start the diswasher</td><td>[Dishwasher door is closed]</td><td>Lock the dishwasher door and set the counter = 1</td></tr>
        <tr><td>Idle</td><td>Drain</td><td>Start the diswasher</td><td>[Dishwasher door is closed]</td><td>Lock the dishwasher door and set the counter = 1</td></tr>
        </table>```""",


        "hierarchical_table":"""```<table border="1">
        <tr><th>Superstate</th><th>Substate</th></tr>
        <tr><td>DishwasherOn</td><td>Door</td></tr>
        <tr><td>DishwasherOn</td><td>Washer</td></tr>
        <tr><td>Door</td><td>Open</td></tr>
        <tr><td>Door</td><td>Closed</td></tr>
        <tr><td>Door</td><td>Locked</td></tr>
        <tr><td>Washer</td><td>Idle</td></tr>
        <tr><td>Washer</td><td>Cleaning</td></tr>
        <tr><td>Washer</td><td>Drying</td></tr>
        <tr><td>Washer</td><td>Suspended</td></tr>
        <tr><td>Cleaning</td><td>Intake</td></tr>
        <tr><td>Cleaning</td><td>Washing</td></tr>
        <tr><td>Cleaning</td><td>Drain</td></tr>
        </table>```""",

         "events_table": """```html<table border="1">
        <tr><th>EventName</th></tr>
        <tr><td>Turn dishwasher on</td></tr>
        <tr><td>Toggle dishwasher program</td></tr>
        <tr><td>Toggle dishwasher drying runtime</td></tr>
        <tr><td>Start the Dishwasher</td></tr>
        <tr><td>Dishwasher is washing</td></tr>
        <tr><td>Dishwasher Waiting</td></tr>
        <tr><td>Dishwasher Draining</td></tr>
        <tr><td>Dishwasher Paused</td></tr>
        <tr><td>Dishwasher Drying</td></tr>
        <tr><td>Stop Dishwasher Drying</td></tr>
        <tr><td>Dishwasher resumed using the same settings</td></tr>
        <tr><td>Open Dishwasher Door</td></tr>
        <tr><td>Close Dishwasher Door</td></tr>
        <tr><td>Lock the dishwasher Door</td></tr>
        </table>```""",

        "transitions_table": """```html<table border="1">
        <tr><th>From State</th><th>To State</th><th>Event</th><th>Guard</th><th>Action</th></tr>
        <tr><td>Open</td><td>Closed</td><td>Close Dishwasher Door</td><td>NONE</td><td>NONE</td></tr>
        <tr><td>Closed</td><td>Open</td><td>Open Dishwasher Door</td><td>NONE</td><td>NONE</td></tr>
        <tr><td>Closed</td><td>Locked</td><td>Lock the dishwasher Door</td><td>NONE</td><td>NONE</td></tr>
        <tr><td>Locked</td><td>Closed</td><td>Unlock the dishwasher Door</td><td>NONE</td><td>NONE</td></tr>
        <tr><td>Idle</td><td>Idle</td><td>Toggle dishwasher program</td><td>[Program number >= 1]</td><td>Diswasher repetitions = Program Number</td></tr>
        <tr><td>Idle</td><td>Idle</td><td>Toggle dishwasher drying time</td><td>NONE</td><td>if drying time equal to 20 then set it to 40 otherwise set it to 20</td></tr>
        <tr><td>Idle</td><td>Cleaning</td><td>Start the diswasher</td><td>[Dishwasher door is closed]</td><td>Lock the dishwasher door and set the counter = 1</td></tr>
        <tr><td>Intake</td><td>Washing</td><td>Dishwasher is washing</td><td>NONE</td><td>NONE</td></tr>
        <tr><td>Washing</td><td>Drain</td><td>Dishwasher Draining</td><td>[After 10 minutes of washing]</td><td>NONE</td></tr>
        <tr><td>Drain</td><td>Intake</td><td>Dishwasher Draining</td><td>[Counter of wash cycles is less than program number]</td><td>NONE</td></tr>
        <tr><td>Cleaning</td><td>Cleaning</td><td>Toggle dishwasher drying time</td><td>NONE</td><td>if drying time equal to 20 then set it to 40 otherwise set it to 20</td></tr>
        <tr><td>Cleaning</td><td>Drying</td><td>Unlock the dishwasher Door</td><td>NONE</td><td>NONE</td></tr>
        <tr><td>Drying</td><td>Suspended</td><td>Open Dishwasher Door</td><td>NONE</td><td>NONE</td></tr>
        <tr><td>Suspended</td><td>Drying</td><td>Close Dishwasher Door</td><td>NONE</td><td>NONE</td></tr>
        <tr><td>Suspended</td><td>Idle</td><td>Dishwasher Waiting</td><td>[After 5 minutes of Dishwasher Paused]</td><td>NONE</td></tr>
        <tr><td>Drying</td><td>Idle</td><td>Dishwasher Waiting</td><td>[After drying time is passed]</td><td>NONE</td></tr>
        <tr><td>Drying</td><td>Drying</td><td>Extend Dishwasher Drying Time</td><td>NONE</td><td>Extend Drying Time to 40 minutes</td></tr>
        </table>```""",

        "superstate_inspected": "Cleaning",

        "substates_inspected": "['Intake', 'Washing', 'Drain']",

        "superstate_initial_state": "Intake",

        "superstate_inspected_for_history_state": "Cleaning",

        "substates_inspected_for_history_state": "['Intake', 'Washing', 'Drain']",

        "history_state_table": """```html<table border="1">
        <tr><th>From State</th><th>Event</th><th>Guard</th><th>Action</th></tr>
        <tr><td>Cleaning</td><td>Toggle dishwasher drying time</td><td>NONE</td><td>if drying time equal to 20 then set it to 40 otherwise set it to 20</td></tr>
        </table>```""",
    },
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
        <tr><th>EventName</th></tr>
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
        <tr><th>From State</th><th>To State</th><th>Event</th><th>Guard</th><th>Action</th></tr>
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
        <tr><th>From State</th><th>To State</th><th>Event</th><th>Guard</th><th>Action</th></tr>
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
        <tr><th>From State</th><th>Event</th><th>Guard</th><th>Action</th></tr>
        <tr><td>Suspended</td><td>resume</td><td>NONE</td><td>NONE</td></tr>
        </table>```""",
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
