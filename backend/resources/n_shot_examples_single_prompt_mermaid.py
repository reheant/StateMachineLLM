from state_machine_descriptions import *

n_shot_examples = {
    "printer_winter_2017": {
        "system_description": printer_winter_2017,
        "mermaid_code_solution": """stateDiagram-v2
    
    state Off
    [*] --> Off
    Off --> On : on
    On --> Off : off
    
    state On {
        state Idle
        [*] --> Idle
        
        Idle --> Idle : login(cardID) [!idAuthorized(cardID)]
        state Ready
        Idle --> Ready : login(cardID) [idAuthorized(cardID)] / {action="none"}

        Ready --> Idle : logoff
        Ready --> Ready : start [action=="scan" && !originalLoaded()]
        Ready --> Ready : start [action=="print" && !documentInQueue()]
        Ready --> Ready : scan / {action="scan"}
        Ready --> Ready : print / {action="print"}
        Ready --> ScanAndEmail : start [action=="scan" && originalLoaded()]
        Ready --> Print : start [action=="print" && documentInQueue()]

        state Busy {

            state ScanAndEmail

            state Print
            
            state HistoryState1
            
            Print --> Suspended : outOfPaper

        }
       
        Busy --> Suspended : jam
        Busy --> Ready : stop
        Busy --> Ready : done

        state Suspended
        Suspended --> Ready : cancel
        Suspended --> HistoryState1 : resume

    }""",
    },
    "spa_manager_winter_2018": {
        "system_description": spa_manager_winter_2018,
        "mermaid_code_solution": """stateDiagram-v2

    state SpaManager {
        --
        state Jacuzzi {
            
            State JacuzziOff
            
            [*] --> JacuzziOff

            JacuzziOff --> JacuzziOn : on

            state JacuzziOn {
                
                State Level1
                
                [*] --> Level1
                
                State Level2
                State Level3

                Level1 --> Level2 : up
                Level2 --> Level3 : up
                Level2 --> Level1 : down
                Level3 --> Level2 : down
                State HistoryState1
            }

            JacuzziOn --> HistoryState1 : setPattern(PatternType type)
            
            JacuzziOn --> JacuzziOff : off
            
            State Paused 
            
            JacuzziOn --> Paused : pause
            Paused --> HistoryState1 : after2min
            Paused --> JacuzziOff : off

        }
        --
        state Sauna {
            State SaunaOff
            [*] --> SaunaOff

            SaunaOff --> SaunaOn : on

            state SaunaOn {
                --
                state Heater {
                    State Head
                    [*] --> Heat
                    
                    State Idle

                    Heat --> Idle : [temp>=90]
                    Idle --> Heat : [temp < 85]
                }
                --
                state Fan {
                    State FanOff
                    [*] --> FanOff
                    
                    State FanOn
                    FanOff --> FanOn : [humidity > 0.40 && exceedTime>3]
                    FanOn --> FanOff : after5min
                }
                --
                state Water {
                    State WaterIdle
                    [*] --> WaterIdle

                    WaterIdle --> WaterIdle : disperse [humidity<0.04 && !Fan.On && timeSinceLast>15]
                }
            }

            SaunaOn --> SaunaOff : off
        }
    }""",
    },
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
