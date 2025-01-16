from resources.state_machine_descriptions import printer_winter_2017, spa_manager_winter_2018

n_shot_examples = {

    # printer system, ECSE 223 Winter 2017 Midterm #2 example
    "Printer": {
        "system_description": printer_winter_2017,
        "initial_state": "Off",
        "transitions_events_table": """<table border="1"><tr><th>Current State</th><th>Event</th><th>Next State(s)</th></tr><tr><td>Off</td><td>Turn On</td><td>On</td></tr><tr><td>On</td><td>Turn Off</td><td>Off</td></tr><tr><td>Idle</td><td>User Login with Unauthorized Card</td><td>Idle</td></tr><tr><td>Idle</td><td>User Login with Authorized Card</td><td>Ready</td></tr><tr><td>Ready</td><td>User Logoff</td><td>Idle</td></tr><tr><td>Ready</td><td>Start Scan without Document</td><td>Ready (Error)</td></tr><tr><td>Ready</td><td>Start Print with Empty Queue</td><td>Ready (Error)</td></tr><tr><td>Ready</td><td>Select Scan Option</td><td>Ready</td></tr><tr><td>Ready</td><td>Select Print Option</td><td>Ready</td></tr><tr><td>Ready</td><td>Start Scan with Document Loaded</td><td>ScanAndEmail</td></tr><tr><td>Ready</td><td>Start Print with Document in Queue</td><td>Print</td></tr><tr><td>ScanAndEmail</td><td>Scan Complete</td><td>Ready</td></tr><tr><td>Print</td><td>Out of Paper</td><td>Suspended</td></tr><tr><td>Print</td><td>Paper Jam</td><td>Suspended</td></tr><tr><td>Print</td><td>Stop Printing</td><td>Ready</td></tr><tr><td>Print</td><td>Print Complete</td><td>Ready</td></tr><tr><td>Suspended</td><td>Cancel Task</td><td>Ready</td></tr><tr><td>Suspended</td><td>Resume Task</td><td>Previous State (Print or Scan)</td></tr></table>""",
        "transitions_events_guards_table": """<table border="1"><tr><th>From State</th><th>To State</th><th>Event</th><th>Guard</th></tr><tr><td>Off</td><td>On</td><td>on</td><td>NONE</td></tr><tr><td>On</td><td>Off</td><td>off</td><td>NONE</td></tr><tr><td>Idle</td><td>Idle</td><td>login</td><td>!idAuthorized(cardID)</td></tr><tr><td>Idle</td><td>Ready</td><td>login</td><td>idAuthorized(cardID)</td></tr><tr><td>Ready</td><td>Idle</td><td>logoff</td><td>NONE</td></tr><tr><td>Ready</td><td>Ready</td><td>start</td><td>action=="scan"&&!originalLoaded()</td></tr><tr><td>Ready</td><td>Ready</td><td>start</td><td>action=="print"&&!documentInQueue()</td></tr><tr><td>Ready</td><td>Ready</td><td>scan</td><td>NONE</td></tr><tr><td>Ready</td><td>Ready</td><td>print</td><td>NONE</td></tr><tr><td>Ready</td><td>ScanAndEmail</td><td>start</td><td>action=="scan"&&originalLoaded()</td></tr><tr><td>Ready</td><td>Print</td><td>start</td><td>action=="print"&&documentInQueue()</td></tr><tr><td>Print</td><td>Suspended</td><td>outOfPaper</td><td>NONE</td></tr><tr><td>Print</td><td>Suspended</td><td>jam</td><td>NONE</td></tr><tr><td>Print</td><td>Ready</td><td>stop</td><td>NONE</td></tr><tr><td>Print</td><td>Ready</td><td>done</td><td>NONE</td></tr><tr><td>Suspended</td><td>Ready</td><td>cancel</td><td>NONE</td></tr><tr><td>Suspended</td><td>Busy (history)</td><td>resume</td><td>NONE</td></tr></table>""",
        "transitions_events_guards_actions_table": """<table border="1"><tr><th>From State</th><th>To State</th><th>Event</th><th>Guard</th><th>Action</th></tr><tr><td>Off</td><td>On</td><td>on</td><td>NONE</td><td>NONE</td></tr><tr><td>On</td><td>Off</td><td>off</td><td>NONE</td><td>NONE</td></tr><tr><td>Idle</td><td>Idle</td><td>login(cardID)</td><td>!idAuthorized(cardID)</td><td>NONE</td></tr><tr><td>Idle</td><td>Ready</td><td>login(cardID)</td><td>idAuthorized(cardID)</td><td>action="none";</td></tr><tr><td>Ready</td><td>Idle</td><td>logoff</td><td>NONE</td><td>NONE</td></tr><tr><td>Ready</td><td>Ready</td><td>start</td><td>action=="scan" && !originalLoaded()</td><td>NONE</td></tr><tr><td>Ready</td><td>Ready</td><td>start</td><td>action=="print" && !documentInQueue()</td><td>NONE</td></tr><tr><td>Ready</td><td>Ready</td><td>scan</td><td>NONE</td><td>action="scan";</td></tr><tr><td>Ready</td><td>Ready</td><td>print</td><td>NONE</td><td>action="print";</td></tr><tr><td>Ready</td><td>ScanAndEmail</td><td>start</td><td>action=="scan" && originalLoaded()</td><td>NONE</td></tr><tr><td>Ready</td><td>Print</td><td>start</td><td>action=="print" && documentInQueue()</td><td>NONE</td></tr><tr><td>Busy</td><td>Suspended</td><td>jam</td><td>NONE</td><td>NONE</td></tr><tr><td>Busy</td><td>Ready</td><td>stop</td><td>NONE</td><td>NONE</td></tr><tr><td>Busy</td><td>Ready</td><td>done</td><td>NONE</td><td>NONE</td></tr><tr><td>Print</td><td>Suspended</td><td>outOfPaper</td><td>NONE</td><td>NONE</td></tr><tr><td>Suspended</td><td>Ready</td><td>cancel</td><td>NONE</td><td>NONE</td></tr></table>""",
        "transitions_events_guards_actions_history_table": """<table border="1"><tr><th>From State</th><th>To State</th><th>Event</th><th>Guard</th><th>Action</th></tr><tr><td>Off</td><td>On</td><td>on</td><td>NONE</td><td>NONE</td></tr><tr><td>On</td><td>Off</td><td>off</td><td>NONE</td><td>NONE</td></tr><tr><td>Idle</td><td>Idle</td><td>login</td><td>!idAuthorized(cardID)</td><td>NONE</td></tr><tr><td>Idle</td><td>Ready</td><td>login</td><td>idAuthorized(cardID)</td><td>action="none";</td></tr><tr><td>Ready</td><td>Idle</td><td>logoff</td><td>NONE</td><td>NONE</td></tr><tr><td>Ready</td><td>Ready</td><td>start</td><td>action=="scan"&&!originalLoaded()</td><td>NONE</td></tr><tr><td>Ready</td><td>Ready</td><td>start</td><td>action=="print"&&!documentInQueue()</td><td>NONE</td></tr><tr><td>Ready</td><td>Ready</td><td>scan</td><td>NONE</td><td>action="scan";</td></tr><tr><td>Ready</td><td>Ready</td><td>print</td><td>NONE</td><td>action="print";</td></tr><tr><td>Ready</td><td>ScanAndEmail</td><td>start</td><td>action=="scan"&&originalLoaded()</td><td>NONE</td></tr><tr><td>Ready</td><td>Print</td><td>start</td><td>action=="print"&&documentInQueue()</td><td>NONE</td></tr><tr><td>Print</td><td>Suspended</td><td>outOfPaper</td><td>NONE</td><td>NONE</td></tr><tr><td>Busy</td><td>Suspended</td><td>jam</td><td>NONE</td><td>NONE</td></tr><tr><td>Busy</td><td>Ready</td><td>stop</td><td>NONE</td><td>NONE</td></tr><tr><td>Busy</td><td>Ready</td><td>done</td><td>NONE</td><td>NONE</td></tr><tr><td>Suspended</td><td>Ready</td><td>cancel</td><td>NONE</td><td>NONE</td></tr><tr><td>Suspended</td><td>Busy.H</td><td>resume</td><td>NONE</td><td>NONE</td></tr></table>""",
        "hierarchical_state_table": """<table border="1"><tr><th>Superstate</th><th>Substate</th></tr><tr><td>Printer</td><td>Off</td></tr><tr><td>Printer</td><td>On</td></tr><tr><td>On</td><td>Idle</td></tr><tr><td>On</td><td>Ready</td></tr><tr><td>On</td><td>Busy</td></tr><tr><td>On</td><td>Suspended</td></tr><tr><td>Busy</td><td>ScanAndEmail</td></tr><tr><td>Busy</td><td>Print</td></tr></table>""",
        "parallel_states_table": """EMPTY"""
    },

    # spa manager system, ECSE 223 Winter 2018 Midterm #2 example
    "Spa Manager": {
        "system_description": spa_manager_winter_2018,
        "initial_state": "Off",
        "transitions_events_table": """<table border="1"> <tr> <th>Current State</th> <th>Event</th> <th>Next State(s)</th> </tr> <tr> <td>JacuzziOff</td> <td>on</td> <td>JacuzziOn</td> </tr> <tr> <td>JacuzziOn</td> <td>off</td> <td>JacuzziOff</td> </tr> <tr> <td>Jacuzzi Level1</td> <td>up</td> <td>Jacuzzi Level2</td> </tr> <tr> <td>Jacuzzi Level2</td> <td>up</td> <td>Jacuzzi Level3</td> </tr> <tr> <td>Jacuzzi Level2</td> <td>down</td> <td>Jacuzzi Level1</td> </tr> <tr> <td>Jacuzzi Level3</td> <td>down</td> <td>Jacuzzi Level2</td> </tr> <tr> <td>JacuzziOn</td> <td>pause</td> <td>Jacuzzi Paused</td> </tr> <tr> <td>JacuzziOn</td> <td>setPattern</td> <td>Jacuzzi H</td> </tr> <tr> <td>Jacuzzi Paused</td> <td>off</td> <td>JacuzziOff</td> </tr> <tr> <td>Jacuzzi Paused</td> <td>resume</td> <td>Jacuzzi H</td> </tr> <tr> <td>Sauna Off</td> <td>on</td> <td>Sauna On</td> </tr> <tr> <td>Sauna On</td> <td>off</td> <td>Sauna Off</td> </tr> <tr> <td>Sauna Heat</td> <td>reachHighTemp</td> <td>Sauna Idle</td> </tr> <tr> <td>Sauna Idle</td> <td>reachLowTemp</td> <td>Sauna Heat</td> </tr> <tr> <td>Sauna Fan Off</td> <td>startFan</td> <td>Sauna Fan On</td> </tr> <tr> <td>Sauna Fan On</td> <td>stopFan</td> <td>Sauna Fan Off</td> </tr> <tr> <td>Sauna Water Idle</td> <td>disperseWater</td> <td>Sauna Water Idle</td> </tr></table>""",
        "transitions_events_guards_table": """<table border="1"> <tr> <th>From State</th> <th>To State</th> <th>Event</th> <th>Guard</th> </tr> <tr> <td>JacuzziOff</td> <td>JacuzziOn</td> <td>on</td> <td></td> </tr> <tr> <td>JacuzziOn</td> <td>JacuzziOff</td> <td>off</td> <td></td> </tr> <tr> <td>Jacuzzi Level1</td> <td>Jacuzzi Level2</td> <td>up</td> <td></td> </tr> <tr> <td>Jacuzzi Level2</td> <td>Jacuzzi Level3</td> <td>up</td> <td></td> </tr> <tr> <td>Jacuzzi Level2</td> <td>Jacuzzi Level1</td> <td>down</td> <td></td> </tr> <tr> <td>Jacuzzi Level3</td> <td>Jacuzzi Level2</td> <td>down</td> <td></td> </tr> <tr> <td>JacuzziOn</td> <td>Jacuzzi Paused</td> <td>pause</td> <td></td> </tr> <tr> <td>JacuzziOn</td> <td>Jacuzzi H</td> <td>setPattern</td> <td></td> </tr> <tr> <td>Jacuzzi Paused</td> <td>JacuzziOff</td> <td>off</td> <td></td> </tr> <tr> <td>Jacuzzi Paused</td> <td>Jacuzzi H</td> <td>resume</td> <td></td> </tr> <tr> <td>Sauna Off</td> <td>Sauna On</td> <td>on</td> <td></td> </tr> <tr> <td>Sauna On</td> <td>Sauna Off</td> <td>off</td> <td></td> </tr> <tr> <td>Sauna Heat</td> <td>Sauna Idle</td> <td>reachHighTemp</td> <td>temp >= 90</td> </tr> <tr> <td>Sauna Idle</td> <td>Sauna Heat</td> <td>reachLowTemp</td> <td>temp &lt; 85</td> </tr> <tr> <td>Sauna Fan Off</td> <td>Sauna Fan On</td> <td>startFan</td> <td>humidity &gt; 0.40 && exceedTime &gt; 3</td> </tr> <tr> <td>Sauna Fan On</td> <td>Sauna Fan Off</td> <td>stopFan</td> <td></td> </tr> <tr> <td>Sauna Water Idle</td> <td>Sauna Water Idle</td> <td>disperseWater</td> <td>humidity &lt; 0.04 && !Fan On && timeSinceLast &gt; 15</td> </tr></table>""",
        "transitions_events_guards_actions_table": """<table border="1"> <tr> <th>From State</th> <th>To State</th> <th>Event</th> <th>Guard</th> <th>Actions</th> </tr> <tr> <td>JacuzziOff</td> <td>JacuzziOn</td> <td>on</td> <td></td> <td></td> </tr> <tr> <td>JacuzziOn</td> <td>JacuzziOff</td> <td>off</td> <td></td> <td></td> </tr> <tr> <td>Jacuzzi Level1</td> <td>Jacuzzi Level2</td> <td>up</td> <td></td> <td></td> </tr> <tr> <td>Jacuzzi Level2</td> <td>Jacuzzi Level3</td> <td>up</td> <td></td> <td></td> </tr> <tr> <td>Jacuzzi Level2</td> <td>Jacuzzi Level1</td> <td>down</td> <td></td> <td></td> </tr> <tr> <td>Jacuzzi Level3</td> <td>Jacuzzi Level2</td> <td>down</td> <td></td> <td></td> </tr> <tr> <td>JacuzziOn</td> <td>Jacuzzi Paused</td> <td>pause</td> <td></td> <td></td> </tr> <tr> <td>JacuzziOn</td> <td>Jacuzzi H</td> <td>setPattern</td> <td></td> <td>setPattern(PatternType type)</td> </tr> <tr> <td>Jacuzzi Paused</td> <td>JacuzziOff</td> <td>off</td> <td></td> <td></td> </tr> <tr> <td>Jacuzzi Paused</td> <td>Jacuzzi H</td> <td>resume</td> <td></td> <td></td> </tr> <tr> <td>Sauna Off</td> <td>Sauna On</td> <td>on</td> <td></td> <td></td> </tr> <tr> <td>Sauna On</td> <td>Sauna Off</td> <td>off</td> <td></td> <td></td> </tr> <tr> <td>Sauna Heat</td> <td>Sauna Idle</td> <td>reachHighTemp</td> <td>temp >= 90</td> <td></td> </tr> <tr> <td>Sauna Idle</td> <td>Sauna Heat</td> <td>reachLowTemp</td> <td>temp &lt; 85</td> <td></td> </tr> <tr> <td>Sauna Fan Off</td> <td>Sauna Fan On</td> <td>startFan</td> <td>humidity &gt; 0.40 && exceedTime &gt; 3</td> <td></td> </tr> <tr> <td>Sauna Fan On</td> <td>Sauna Fan Off</td> <td>stopFan</td> <td></td> <td></td> </tr> <tr> <td>Sauna Water Idle</td> <td>Sauna Water Idle</td> <td>disperseWater</td> <td>humidity &lt; 0.04 && !Fan On && timeSinceLast &gt; 15</td> <td>disperse</td> </tr></table>""",
        "transitions_events_guards_actions_history_table": """<table border="1"> <tr> <th>From State</th> <th>To State</th> <th>Event</th> <th>Guard</th> <th>Actions</th> </tr> <tr> <td>JacuzziOff</td> <td>JacuzziOn</td> <td>on</td> <td></td> <td></td> </tr> <tr> <td>JacuzziOn</td> <td>JacuzziOff</td> <td>off</td> <td></td> <td></td> </tr> <tr> <td>Jacuzzi Level1</td> <td>Jacuzzi Level2</td> <td>up</td> <td></td> <td></td> </tr> <tr> <td>Jacuzzi Level2</td> <td>Jacuzzi Level3</td> <td>up</td> <td></td> <td></td> </tr> <tr> <td>Jacuzzi Level2</td> <td>Jacuzzi Level1</td> <td>down</td> <td></td> <td></td> </tr> <tr> <td>Jacuzzi Level3</td> <td>Jacuzzi Level2</td> <td>down</td> <td></td> <td></td> </tr> <tr> <td>JacuzziOn</td> <td>Jacuzzi Paused</td> <td>pause</td> <td></td> <td></td> </tr> <tr> <td>JacuzziOn</td> <td>Jacuzzi H</td> <td>setPattern</td> <td></td> <td>setPattern(PatternType type)</td> </tr> <tr> <td>Jacuzzi Paused</td> <td>JacuzziOff</td> <td>off</td> <td></td> <td></td> </tr> <tr> <td>Jacuzzi Paused</td> <td>Jacuzzi H</td> <td>resume</td> <td></td> <td></td> </tr> <tr> <td>Sauna Off</td> <td>Sauna On</td> <td>on</td> <td></td> <td></td> </tr> <tr> <td>Sauna On</td> <td>Sauna Off</td> <td>off</td> <td></td> <td></td> </tr> <tr> <td>Sauna Heat</td> <td>Sauna Idle</td> <td>reachHighTemp</td> <td>temp >= 90</td> <td></td> </tr> <tr> <td>Sauna Idle</td> <td>Sauna Heat</td> <td>reachLowTemp</td> <td>temp &lt; 85</td> <td></td> </tr> <tr> <td>Sauna Fan Off</td> <td>Sauna Fan On</td> <td>startFan</td> <td>humidity &gt; 0.40 && exceedTime &gt; 3</td> <td></td> </tr> <tr> <td>Sauna Fan On</td> <td>Sauna Fan Off</td> <td>stopFan</td> <td></td> <td></td> </tr> <tr> <td>Sauna Water Idle</td> <td>Sauna Water Idle</td> <td>disperseWater</td> <td>humidity &lt; 0.04 && !Fan On && timeSinceLast &gt; 15</td> <td>disperse</td> </tr></table>""",
        "hierarchical_state_table": """<table border="1"> <tr> <th>Superstate</th> <th>Substate</th> </tr><tr> <td>SpaManager</td> <td>Jacuzzi</td> </tr> <tr> <td>Jacuzzi</td> <td>JacuzziOff</td> </tr> <tr> <td>Jacuzzi</td> <td>JacuzziOn</td> </tr> <tr> <td>JacuzziOn</td> <td>Jacuzzi Level1</td> </tr> <tr> <td>JacuzziOn</td> <td>Jacuzzi Level2</td> </tr> <tr> <td>JacuzziOn</td> <td>Jacuzzi Level3</td> </tr> <tr> <td>JacuzziOn</td> <td>Jacuzzi Paused</td> </tr> <tr> <td>JacuzziOn</td> <td>Jacuzzi H</td> </tr><tr> <td>SpaManager</td> <td>Sauna</td> </tr> <tr> <td>Sauna</td> <td>Sauna Off</td> </tr> <tr> <td>Sauna</td> <td>Sauna On</td> </tr> <tr> <td>Sauna On</td> <td>Sauna Heat</td> </tr> <tr> <td>Sauna On</td> <td>Sauna Idle</td> </tr> <tr> <td>Sauna On</td> <td>Sauna Fan Off</td> </tr> <tr> <td>Sauna On</td> <td>Sauna Fan On</td> </tr> <tr> <td>Sauna On</td> <td>Sauna Water Idle</td> </tr></table>""",
        "parallel_states_table": """<table border="1"> <tr> <th>Parallel State<th> <th>Parallel Region</th> <th>Substate</th> </tr> <tr> <td>SpaManager<td> <td>Jacuzzi</td> <td>JacuzziOff</td> </tr> <tr> <td>SpaManager<td> <td>Jacuzzi</td> <td>JacuzziOn</td> </tr> <tr> <td>SpaManager<td> <td>Jacuzzi</td> <td>Paused</td> </tr> <tr> <td>SpaManager<td> <td>Sauna</td> <td>SaunaOff</td> </tr> <tr> <td>SpaManager<td> <td>Sauna</td> <td>SaunaOn</td> </tr> <tr> <td>SaunaOn<td> <td>Heater</td> <td>Heat</td> </tr> <tr> <td>SaunaOn<td> <td>Heater</td> <td>HeaterIdle</td> </tr> <tr> <td>SaunaOn<td> <td>Fan</td> <td>FanOff</td> </tr> <tr> <td>SaunaOn<td> <td>Fan</td> <td>FanOn</td> </tr> <tr> <td>SaunaOn<td> <td>Water</td> <td>WaterIdle</td> </tr></table>"""
    },

    # dishwasher system, ECSE 223 Winter 2019 Midterm #2 example
    "Dishwasher": {
            "system_description":"""
            A dishwasher comes with various programs that govern how the dishwasher cleans dishes. The user
            may select one of the programs, adjust the drying time, and press the start button to start the
            selected program.
            When a dishwasher is started, water is first taken from the water intake pipe. Then, the dishes are
            washed for 10 minutes and the water is drained. These steps are repeated a certain number of times
            depending on the chosen dishwasher program. Afterwards, the dishwasher dries the dishes with hot
            air. By default, the standard drying time of 20 minutes is used. However, the drying time may be
            extended to 40 minutes at any point during the dishwasher program. The drying time may also be
            reduced back to the default time but only as long as the drying phase has not started. When the
            dishwasher is active, its door is locked until the start of the drying phase. It is possible to open the
            door during the drying phase. When this happens, the drying phase is suspended. The drying phase
            continues if the door is closed within 5 minutes of opening it. If the door stays open longer, then the
            dishwasher does not continue with drying the dishes and ends the dishwasher program""",
            "transitions_events_table":
            """<table border="1">
            <tr><th>Current State</th><th>Event</th><th>Next State(s)</th></tr>
            <tr><td>Closed</td><td>open</td><td>Open</td></tr>
            <tr><td>Open</td><td>close</td><td>Closed</td></tr>
            <tr><td>Closed</td><td>lock</td><td>Locked</td></tr>
            <tr><td>Locked</td><td>unlock</td><td>Closed</td></tr>
            <tr><td>Idle</td><td>selectProgram(n) [n>=1]</td><td>Idle</td></tr>
            <tr><td>Idle</td><td>toggleDryingTime</td><td>Idle</td></tr>
            <tr><td>Idle</td><td>start [door.isClosed()]</td><td>Intake</td></tr>
            <tr><td>Intake</td><td>-</td><td>Washing</td></tr>
            <tr><td>Washing</td><td>after 10 min</td><td>Drain</td></tr>
            <tr><td>Drain</td><td>[c>r]</td><td>Complete</td></tr>
            <tr><td>Drain</td><td>[c<r]</td><td>Intake</td></tr>
            <tr><td>Drying</td><td>close</td><td>Suspended</td></tr>
            <tr><td>Drying</td><td>after dT min</td><td>Idle</td></tr>
            <tr><td>Suspended</td><td>open</td><td>Drying</td></tr>
            <tr><td>Idle</td><td>after 5 min</td><td>Drying</td></tr>
            <tr><td>Drying</td><td>extendDryingTime</td><td>Drying</td></tr>
            </table>""",
            "transitions_events_guards_table":
            """<table border="1">
            <tr><th>From State</th><th>To State</th><th>Event</th><th>Guard</th></tr>
            <tr><td>Closed</td><td>Open</td><td>open</td><td></td></tr>
            <tr><td>Open</td><td>Closed</td><td>close</td><td></td></tr>
            <tr><td>Closed</td><td>Locked</td><td>lock</td><td></td></tr>
            <tr><td>Locked</td><td>Closed</td><td>unlock</td><td></td></tr>
            <tr><td>Idle</td><td>Idle</td><td>selectProgram(n)</td><td>n>=1</td></tr>
            <tr><td>Idle</td><td>Idle</td><td>toggleDryingTime</td><td></td></tr>
            <tr><td>Idle</td><td>Intake</td><td>start</td><td>door.isClosed()</td></tr>
            <tr><td>Intake</td><td>Washing</td><td></td><td></td></tr>
            <tr><td>Washing</td><td>Drain</td><td>after 10 min</td><td></td></tr>
            <tr><td>Drain</td><td>Complete</td><td></td><td>c>=r</td></tr>
            <tr><td>Drain</td><td>Intake</td><td></td><td>c<r</td></tr>
            <tr><td>Drying</td><td>Suspended</td><td>close</td><td></td></tr>
            <tr><td>Drying</td><td>Idle</td><td>after dT min</td><td></td></tr>
            <tr><td>Suspended</td><td>Drying</td><td>open</td><td></td></tr>
            <tr><td>Idle</td><td>Drying</td><td>after 5 min</td><td></td></tr>
            <tr><td>Drying</td><td>Drying</td><td>extendDryingTime</td><td></td></tr>
            <tr><td>Idle</td><td>Idle</td><td>toggleDryingTime</td><td>if dT=20 then dT=40 else dT=20</td></tr>
            </table>""",
            "transitions_events_guards_actions_table":
            """<table border="1">
            <tr><th>From State</th><th>To State</th><th>Event</th><th>Guard</th><th>Actions</th></tr>
            <tr><td>Closed</td><td>Open</td><td>open</td><td></td><td></td></tr>
            <tr><td>Open</td><td>Closed</td><td>close</td><td></td><td></td></tr>
            <tr><td>Closed</td><td>Locked</td><td>lock</td><td></td><td></td></tr>
            <tr><td>Locked</td><td>Closed</td><td>unlock</td><td></td><td></td></tr>
            <tr><td>Idle</td><td>Idle</td><td>selectProgram(n)</td><td>n>=1</td><td>r=n</td></tr>
            <tr><td>Idle</td><td>Idle</td><td>toggleDryingTime</td><td></td><td>if dT=20 then dT=40 else dT=20</td></tr>
            <tr><td>Idle</td><td>Intake</td><td>start</td><td>door.isClosed()</td><td>door.lock(); c=1</td></tr>
            <tr><td>Intake</td><td>Washing</td><td></td><td></td><td></td></tr>
            <tr><td>Washing</td><td>Drain</td><td>after 10 min</td><td></td><td></td></tr>
            <tr><td>Drain</td><td>Complete</td><td></td><td>c>=r</td><td></td></tr>
            <tr><td>Drain</td><td>Intake</td><td></td><td>c<r</td><td>c++</td></tr>
            <tr><td>Drying</td><td>Suspended</td><td>close</td><td></td><td></td></tr>
            <tr><td>Drying</td><td>Idle</td><td>after dT min</td><td></td><td></td></tr>
            <tr><td>Suspended</td><td>Drying</td><td>open</td><td></td><td>door.unlock()</td></tr>
            <tr><td>Idle</td><td>Drying</td><td>after 5 min</td><td></td><td></td></tr>
            <tr><td>Drying</td><td>Drying</td><td>extendDryingTime</td><td></td><td>dT=40</td></tr>
            </table>""",
            "transitions_events_guards_actions_history_table":
            """<table border="1">
            <tr><th>From State</th><th>To State</th><th>Event</th><th>Guard</th><th>Action</th></tr>
            <tr><td>Closed</td><td>Open</td><td>open</td><td>NONE</td><td>NONE</td></tr>
            <tr><td>Open</td><td>Closed</td><td>close</td><td>NONE</td><td>NONE</td></tr>
            <tr><td>Closed</td><td>Locked</td><td>lock</td><td>NONE</td><td>NONE</td></tr>
            <tr><td>Locked</td><td>Closed</td><td>unlock</td><td>NONE</td><td>NONE</td></tr>
            <tr><td>Idle</td><td>Idle</td><td>selectProgram</td><td>n>=1</td><td>r=n;</td></tr>
            <tr><td>Idle</td><td>Idle</td><td>toggleDryingTime</td><td>NONE</td><td>if(dT==20){dT=40;}else{dT=20;}</td></tr>
            <tr><td>Idle</td><td>Intake</td><td>start</td><td>door.isClosed()</td><td>door.lock();c=1;</td></tr>
            <tr><td>Intake</td><td>Washing</td><td>NONE</td><td>NONE</td><td>NONE</td></tr>
            <tr><td>Washing</td><td>Drain</td><td>after10min</td><td>NONE</td><td>NONE</td></tr>
            <tr><td>Drain</td><td>Complete</td><td>NONE</td><td>c>=r</td><td>NONE</td></tr>
            <tr><td>Drain</td><td>Intake</td><td>NONE</td><td>c<r</td><td>c++;</td></tr>
            <tr><td>Drying</td><td>Suspended</td><td>close</td><td>NONE</td><td>NONE</td></tr>
            <tr><td>Drying</td><td>Idle</td><td>afterDTmin</td><td>NONE</td><td>NONE</td></tr>
            <tr><td>Suspended</td><td>Drying</td><td>open</td><td>NONE</td><td>door.unlock();</td></tr>
            <tr><td>Idle</td><td>Drying</td><td>after5min</td><td>NONE</td><td>NONE</td></tr>
            <tr><td>Drying</td><td>Drying</td><td>extendDryingTime</td><td>NONE</td><td>dT=40;</td></tr>
            <tr><td>Cleaning.H</td><td>Intake</td><td>start</td><td>door.isClosed()</td><td>door.lock();c=1;</td></tr>
            </table>""",
            "hierarchical_state_table":
            """<table border="1">
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
            </table>""",
            "parallel_states_table": 
            """<table border="1">
            <tr><th>Parallel State</th><th>Parallel Region</th><th>Substate</th></tr>
            <tr><td>DishwasherOn</td><td>Door</td><td>Open</td></tr>
            <tr><td>DishwasherOn</td><td>Door</td><td>Closed</td></tr>
            <tr><td>DishwasherOn</td><td>Door</td><td>Locked</td></tr>
            <tr><td>DishwasherOn</td><td>Washer</td><td>Idle</td></tr>
            <tr><td>DishwasherOn</td><td>Washer</td><td>Drying</td></tr>
            <tr><td>DishwasherOn</td><td>Washer</td><td>Suspended</td></tr>
            <tr><td>DishwasherOn</td><td>Washer</td><td>Intake</td></tr>
            <tr><td>DishwasherOn</td><td>Washer</td><td>Washing</td></tr>
            <tr><td>DishwasherOn</td><td>Washer</td><td>Drain</td></tr>
            </table>"""
        }
  
      
}


def get_n_shot_examples(keys, fields):
    """
    The get n_shot_examples function takes in keys (a list of system names, e.g., ["Spa Manager"]),
    and fields (a list of system descriptors, e.g., ["system_description", "hierarchical_state_table"])
    to provide n-shot prompting examples for prompts in the SMF prompts
    """
    result = ""
    for i, key in enumerate(keys):
        if key in n_shot_examples:
            result += f"Example {i+1}: {key}\n"
            for field in fields:
                result += f"\n{field}: {n_shot_examples[key][field]}\n"
            result += "\n"
    return result.strip()
