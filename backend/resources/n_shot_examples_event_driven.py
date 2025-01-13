from resources.state_machine_descriptions import *

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
    },
    "spa_manager_winter_2018": {
        # NEEDS TO BE COMPLETED OPEN ANOTHER ISSUE
        "system_description": spa_manager_winter_2018,
        "system_name": "SpaManager",
        "states_table": """<table border="1">
        <tr><th>StateName</th></tr>
        <tr><th>JacuzziOff</th></tr>
        <tr><td>Level1</td></tr>
        <tr><td>Level2</td></tr>
        <tr><td>Level3</td></tr>
        <tr><td>JacuzziPaused</td></tr>
        <tr><td>SaunaOff</td></tr>
        <tr><td>HeaterHeating</td></tr>
        <tr><td>HeaterIdle</td></tr>
        <tr><td>FanOff</td></tr>
        <tr><td>FanOn</td></tr>
        <tr><td>WaterIdle</td></tr>
        </table>""",

        "initial_state": "JacuzziOff",

        "events_table": """<table border="1">
        <table border="1">
        <tr><th>EventName</th></tr>
        <!-- Jacuzzi Events -->
        <tr><td>Turn Jacuzzi On</td></tr>
        <tr><td>Turn Jacuzzi Off</td></tr>
        <tr><td>Set Pattern Level 1</td></tr>
        <tr><td>Set Pattern Level 2</td></tr>
        <tr><td>Set Pattern Level 3</td></tr>
        <tr><td>Pattern Level Up</td></tr>
        <tr><td>Pattern Level Down</td></tr>
        <tr><td>Pause Jacuzzi</td></tr>
        <tr><td>Resume Jacuzzi from Pause</td></tr>
        <tr><td>2 Minutes Elapsed (Auto-Pause)</td></tr>
        <tr><td>Set Pattern Type</td></tr>
        
        <!-- Sauna Events -->
        <tr><td>Turn Sauna On</td></tr>
        <tr><td>Turn Sauna Off</td></tr>
        <tr><td>Temperature Exceeds 90°C</td></tr>
        <tr><td>Temperature Falls Below 85°C</td></tr>
        <tr><td>Turn Heater On</td></tr>
        <tr><td>Heater Goes to Idle</td></tr>
        
        <!-- Fan Events -->
        <tr><td>Turn Fan On</td></tr>
        <tr><td>Turn Fan Off</td></tr>
        <tr><td>Humidity Above 40% for 3+ Minutes</td></tr>
        <tr><td>5 Minutes Elapsed (Fan Auto-Off)</td></tr>
        
        <!-- Water Events -->
        <tr><td>Water System to Idle</td></tr>
        <tr><td>Disperse Water</td></tr>
        <tr><td>Humidity Below 40%</td></tr>
        <tr><td>15 Minutes Since Last Water Dispersion</td></tr>
        </table>""",

        "state_inspected": "Level2",

        "associated_events": "Turn Jacuzzi Off, Pattern Level Up, Pattern Level Down, Set Pattern Type, Pause Jacuzzi",

        "event_inspected": "Pattern Level Up",

         "create_transitions": """```html<table border="1">
        <tr><th>From State</th><th>To State</th><th>Event</th><th>Guard</th><th>Action</th></tr>
        <tr><td rowspan="3">Level2</td><td>Level3</td><td>Pattern Level Up</td><td>NONE</td><td>NONE</td></tr>
        </table>```""",

        "hierarchical_table":"""```
        <table border="1">
        <tr><th>Superstate</th><th>Substate</th></tr>
        <!-- Jacuzzi section -->
        <tr><td>SpaManager</td><td>Jacuzzi</td></tr>
        <tr><td>Jacuzzi</td><td>JacuzziOff</td></tr>
        <tr><td>Jacuzzi</td><td>JacuzziOn</td></tr>
        <tr><td>Jacuzzi</td><td>JacuzziPaused</td></tr>
        <tr><td>JacuzziOn</td><td>Level1</td></tr>
        <tr><td>JacuzziOn</td><td>Level2</td></tr>
        <tr><td>JaczziOn</td><td>Level3</td></tr>
        
        <!-- Sauna section -->
        <tr><td>SpaManager</td><td>Sauna</td></tr>
        <tr><td>Sauna</td><td>SaunaOff</td></tr>
        <tr><td>Sauna</td><td>SaunaOn</td></tr>
        <tr><td>SaunaOn</td><td>Heater</td></tr>
        <tr><td>SaunaOn</td><td>Fan</td></tr>
        <tr><td>SaunaOn</td><td>Water</td></tr>
        <tr><td>Heater</td><td>HeaterHeating</td></tr>
        <tr><td>Heater</td><td>HeaterIdle</td></tr>
        <tr><td>Fan</td><td>FanOff</td></tr>
        <tr><td>Fan</td><td>FanOn</td></tr>
        <tr><td>Water</td><td>WaterIdle</td></tr>
        </table>```""",

        "transitions_table": """```
        html<table border="1">
        <tr><th>From State</th><th>To State</th><th>Event</th><th>Guard</th><th>Action</th></tr>
        
        <!-- Jacuzzi transitions -->
        <tr><td>JacuzziOff</td><td>JacuzziOn</td><td>Turn Jacuzzi On</td><td>NONE</td><td>NONE</td></tr>
        <tr><td>JacuzziOn</td><td>JacuzziOff</td><td>Turn Jacuzzi Off</td><td>NONE</td><td>NONE</td></tr>
        <tr><td>JacuzziOn</td><td>JacuzziPaused</td><td>Pause Jacuzzi</td><td>NONE</td><td>NONE</td></tr>
        <tr><td>Level1</td><td>Level2</td><td>Pattern Level Up</td><td>NONE</td><td>NONE</td></tr>
        <tr><td>Level2</td><td>Level1</td><td>Pattern Level Down</td><td>NONE</td><td>NONE</td></tr>
        <tr><td>Level2</td><td>Level3</td><td>Pattern Level Up</td><td>NONE</td><td>NONE</td></tr>
        <tr><td>Level3</td><td>Level2</td><td>Pattern Level Down</td><td>NONE</td><td>NONE</td></tr>
    
        <tr><td>Level1</td><td>JacuzziPaused</td><td>2 Minutes Elapsed (Auto-Pause)</td><td>NONE</td><td>NONE</td></tr>
        <tr><td>Level2</td><td>JacuzziPaused</td><td>2 Minutes Elapsed (Auto-Pause)</td><td>NONE</td><td>NONE</td></tr>
        <tr><td>Level3</td><td>JacuzziPaused</td><td>2 Minutes Elapsed (Auto-Pause)</td><td>NONE</td><td>NONE</td></tr>
        <tr><td>JacuzziPaused</td><td>JacuzziOff</td><td>Turn Jacuzzi Off</td><td>NONE</td><td>NONE</td></tr>
        
        <!-- Sauna transitions -->
        <tr><td>SaunaOff</td><td>SaunaOn</td><td>Turn Sauna On</td><td>NONE</td><td>NONE</td></tr>
        <tr><td>SaunaOn</td><td>SaunaOff</td><td>Turn Sauna Off</td><td>NONE</td><td>NONE</td></tr>
        
        <!-- Heater transitions -->
        <tr><td>HeaterHeating</td><td>HeaterIdle</td><td>Temperature Exceeds 90°C</td><td>NONE</td><td>NONE</td></tr>
        <tr><td>HeaterIdle</td><td>HeaterHeating</td><td>Temperature Falls Below 85°C</td><td>NONE</td><td>NONE</td></tr>
        
        
        <!-- Fan transitions -->
        <tr><td>FanOff</td><td>FanOn</td><td>Humidity Above 40% for 3+ Minutes</td><td>NONE</td><td>NONE</td></tr>
        <tr><td>FanOn</td><td>FanOff</td><td>5 Minutes Elapsed (Fan Auto-Off)</td><td>NONE</td><td>NONE</td></tr>
        
        <!-- Water transitions -->
        <tr><td>WaterIdle</td><td>WaterIdle</td><td>Disperse Water</td><td>[Humidity Below 40% && !Fan.On && 15 Minutes Since Last Water Dispersion]</td><td>NONE</td></tr>
        
        </table>```""",

        "superstate_inspected": "JacuzziOn",

        "substates_inspected": "['Level1', 'Level2', 'Level3']",

        "superstate_initial_state": "Level1",

        "superstate_inspected_for_history_state": "JacuzziOn",

        "substates_inspected_for_history_state": "['Level1', 'Level2', Level3]",

        "history_state_table": """```html<table border="1"> 
        <tr><th>From State</th><th>Event</th><th>Guard</th><th>Action</th></tr>
        <tr><td>JacuzziOn</td><td>Set Pattern Type</td><td>NONE</td><td>NONE</td></tr>
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
