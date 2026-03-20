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

        state Busy {
            state ScanAndEmail

            state Print
            
            state H
            
            ScanAndEmail --> Ready : stop
            ScanAndEmail --> Ready : done
            Print --> Ready : stop
            Print --> Ready : done
            Print --> Suspended : outOfPaper
        }
        
        Ready --> ScanAndEmail : start [action=="scan" && originalLoaded()]
        Ready --> Print : start [action=="print" && documentInQueue()]
       
        Busy --> Suspended : jam

        state Suspended
        Suspended --> Ready : cancel
        Suspended --> H : resume

    }""",
    },
    "spa_manager_winter_2018": {
        "system_description": spa_manager_winter_2018,
        "mermaid_code_solution": """stateDiagram-v2

    state SpaManager {
        region Jacuzzi {

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
                State H
            }

            JacuzziOn --> H : setPattern(PatternType type)

            JacuzziOn --> JacuzziOff : off

            State Paused

            JacuzziOn --> Paused : pause
            Paused --> H : after2min
            Paused --> JacuzziOff : off

        }
        region Sauna {
            State SaunaOff
            [*] --> SaunaOff

            SaunaOff --> SaunaOn : on

            state SaunaOn {
                region Heater {
                    State Heat
                    [*] --> Heat

                    State Idle

                    Heat --> Idle : [temp>=90]
                    Idle --> Heat : [temp < 85]
                }
                region Fan {
                    State FanOff
                    [*] --> FanOff

                    State FanOn
                    FanOff --> FanOn : [humidity > 0.40 && exceedTime>3]
                    FanOn --> FanOff : after5min
                }
                region Water {
                    State WaterIdle
                    [*] --> WaterIdle

                    WaterIdle --> WaterIdle : disperse [humidity<0.04 && !Fan.On && timeSinceLast>15]
                }
            }

            SaunaOn --> SaunaOff : off
        }
    }""",
    },
    "dishwasher_winter_2019": {
        "system_description": dishwasher_winter_2019,
        "mermaid_code_solution": """stateDiagram-v2
       
    state DishwasherOn {
        region Door {
            State Closed
            State Open
            State Locked

            [*] --> Closed
            Closed --> Open : open
            Closed --> Locked : lock
            Open --> Closed : close
            Locked --> Closed : unlock
        }
        region Washer {
            State Idle
            [*] --> Idle
            Idle --> Idle : selectProgram(n) [n >= 1] / [r=n]
            Idle --> Idle : toggleDryingTime / [if (dT=20) dT=40 else dT = 20]
            Idle --> Cleaning : start [door.isClosed()] / [door.lock() c=1]

            state Suspended
            Suspended --> Drying : close
            Suspended --> Idle : after(5)

            state Drying
            Drying --> Drying : extendDryingTime / [dT=40]
            Drying --> Suspended : open
            Drying --> Idle : after(dT)

            state Cleaning {
                state Intake
                state Washing
                state Drain
                state FinalCleaning
                state H
                
                [*] --> Intake
                Intake --> Washing : entry
                Washing --> Drain : after(10min)
                Drain --> Intake : [c < r] / [c++]
                Drain --> FinalCleaning : [c >= r]
                FinalCleaning --> Drying : entry / [door.unlock()]
            }

            Cleaning --> H : toggleDryingTime / [if (dT=20) dT=40 else dT = 20]
            Cleaning --> Drying : / door.unlock()
        }
    }""",
    },
    "chess_clock_fall_2019": {
        "system_description": chess_clock_fall_2019,
        "mermaid_code_solution": """
        stateDiagram-v2
        state Off
        [*] --> Off

        state On {
            
            state GameSetup {
                region TimingSelection {
                    state TimingSelectionState
                    [*] --> TimingSelectionState
                    TimingSelectionState --> TimingSelectionState : plus / {incrTimingProgram()}
                    TimingSelectionState --> TimingSelectionState : minus / {decrTimingProgram()}
                }
                region WhiteKingStatus {
                    state WhiteKingOnLeft
                    state WhiteKingOnRight
                    [*] --> WhiteKingOnLeft
                    WhiteKingOnLeft --> WhiteKingOnRight : flip
                    WhiteKingOnRight --> WhiteKingOnLeft : flip
                }
            }
            [*] --> GameSetup
            state ReadyToStart
            GameSetup --> ReadyToStart : select
            
            state GameFinished
            state GamePaused
            
            state GameRunning {
                state WhiteClockRunning
                [*] --> WhiteClockRunning

                state BlackClockRunning
                WhiteClockRunning --> WhiteClockRunning : after(1) [wc > 0] / {decrTimer(wc)}
                WhiteClockRunning --> GameFinished : after(1) [wc == 0] / {flashFlag(white)}
                WhiteClockRunning --> BlackClockRunning : flip
                
                note right of WhiteClockRunning
                    entry / {startTimer(wc)}
                    exit / {stopTimer(wc)}
                end note

                BlackClockRunning --> BlackClockRunning : after(1) [bc > 0] / {decrTimer(bc)}
                BlackClockRunning --> GameFinished : after(1) [bc == 0] / {flashFlag(black)}
                BlackClockRunning --> WhiteClockRunning : flip
                
                note right of BlackClockRunning
                    entry / {startTimer(bc)}
                    exit / {stopTimer(bc)}
                end note
                
                state H
                H --> WhiteClockRunning : resume

            }
            ReadyToStart --> GameRunning : startStop
            GameRunning --> GamePaused : startStop
            GamePaused --> GameRunning : startStop
            GamePaused --> H : resume

        }
        Off --> On : onOff
        On --> Off : onOff
        """,
    },
    "automatic_bread_maker_fall_2020": {
        "system_description": automatic_bread_maker_fall_2020,
        "mermaid_code_solution": """stateDiagram-v2
        state Off
        [*] --> Off
        Off --> On : on
        On --> Off : off
        state On {
            [*] --> Setup
            state Setup {
                state Medium
                [*] --> Medium : / delay = 0 then selectFirstCourse()
                state Dark
                Medium --> Dark : crust
                state Light 
                Dark --> Light : crust
                Light --> Medium 
                
                State H
            }
            Setup --> H : menu / selectNextCourse()
            Setup --> H : plus [delay=17*60+50] / delay=delay+10
            Setup --> H : minus [delay>=10] / delay=delay-10
            
            state Countdown
            Setup --> Countdown : start [delay>0]
            Countdown --> Setup : stop
            
            state Baking {
                state Kneading
                [*] --> Kneading
                
                note right of Kneading
                    entry / startKneading()
                    exit / stopKneading()
                end note
                
                state Rising
                Kneading --> Rising : after kneadingTime
                
                state Bake
                Rising --> Bake : after risingTime
                
                note right of Bake
                    do: heat()
                end note
                
                state Warming
                Bake --> Warming : after bakingTime
                
                note right of Warming
                    do: warm()
                end note
    
                Warming --> Setup : after 60min
            }
            
            Countdown --> Baking : after delay / setCourseTime()
            Baking --> Setup : stop
            Setup --> Baking : start [delay=0] / setCourseTime()
        }
    """
    },
    
    "thermomix_fall_2021": {
        "system_description": thermomix_fall_2021,
        "mermaid_code_solution": """stateDiagram-v2
        
        state TransportationMode
        [*] --> TransportationMode

        TransportationMode --> On : selectorPressed

        state PreparingOff
        PreparingOff --> H : selectorReleased
        On --> PreparingOff : selectorHeld
        
        state Off
        PreparingOff --> Off : after5sec

        Off --> On : selectorPressed

        state On {

            state Home
            [*] --> Home
            
            state PreparingShutdown
            Home --> PreparingShutdown : after14min30sec
            PreparingShutdown --> Home : cancel
            PreparingShutdown --> Off : after30sec
            
            state PromptToAdd
            Home --> PromptToAdd : start [!bowlRemoved()] / setIngredients()
            PromptToAdd --> PromptToAdd : next [weightCorrect() && moreIngredientsRequired] / setIngredients()
    
            state Chop
            PromptToAdd --> Chop : next [weightCorrect() && !moreIngredientsRequired] / setChoppingSpeedAndTime()
            Chop --> PromptToAdd : next [choppingTimeDone && moreIngredientsRequired()] / setIngredients()
            
            state Cook
            Chop --> Cook : next [choppingTimeDone && !moreIngredientsRequired()] / setCookingSpeedAndTime()
            Cook --> PromptToAdd : afterChoppingTime [moreIngredientsRequired
            
            state Ready
            Cook --> Ready : afterCookingTime [!moreIngredientsRequired]
            Ready --> PreparingShutdown : after14min30sec
            
            state H
            
        }
        On --> On : bowlRemoved
        """,
    },
    "ATAS_fall_2022": {
        "system_description": ATAS_fall_2022,
        "mermaid_code_solution": """stateDiagram-v2
        state Scheduled
        [*] --> Scheduled

        Scheduled --> Active : atBeginningStopDuration / p0n and setCs

        state Arrived

        state Active {
            region TrainControl {
                state Emergency
                [*] --> TrainMovement
                TrainMovement --> Emergency : emergency / estop
                Emergency --> H : clear
                
                state TrainMovement {
                    state AtStation
                    [*] --> AtStation
                    AtStation --> StopNotRequired : after stopDuration [!stopRequired()]
                    AtStation --> Arrived : after stopDuration [isLastStop()] / pOff
                    
                    note right of AtStation
                        entry / openDoors()
                        exit / closeDoors()
                    end note

                    state StopNotRequired
                    StopNotRequired --> StopNotRequired : enteringSegment [isStationSegment() && !stopRequired()]
                    StopNotRequired --> StopNotRequired : enteringSegment [isRegularSegment()]
                    StopNotRequired --> StopNotRequired : enteringSegment [isTrafficLightSegment() && !isRed()]
                    
                    note right of StopNotRequired
                        entry / setSpeed
                    end note
                    
                    state ApproachingStation
                    StopNotRequired --> ApproachingStation : enteringSegment [isStationSegment() && stopRequired()]
                    ApproachingStation --> AtStation : stopped
                    
                    state ApproachingRedLight
                    StopNotRequired --> ApproachingRedLight : enteringSegment [isTrafficLightSegment() && isRed()]
                    
                    state AtRedTrafficLight
                    ApproachingRedLight --> AtRedTrafficLight : stopped
                    AtRedTrafficLight --> StopNotRequired : green
                    
                    state H
                }

                TrainMovement --> Emergency : emergency / estop

                state Emergency
                Emergency --> TrainMovement : clear
                    
            }

            region SDS {
                state SDSActive
                [*] --> SDSActive

                SDSActive --> SDSActive : after1sec [hasSegmentChanged()] / setCs and enteringSegment()
                SDSActive --> SDSActive : after1sec [!hasSegmentChanged()]
            }
            region MDS {
                state Stopped
                state Moving
                [*] --> Stopped

                Stopped --> Stopped : after1sec [speed == 0]
                Stopped --> Moving : after1sec [speed > 0]
                Moving --> Moving : after1sec [speed > 0]
                Moving --> Stopped : after1sec [speed == 0] / stopped()
            }
            region ODS {
                state ODSActive
                [*] --> ODSActive

                ODSActive --> ODSActive : after1sec [!obstacleDetected()]
                ODSActive --> ODSActive : after1sec [obstacleDetected()] / emergency()
            }
        }""",
    },
        "WUMPLE_fall_2023_Version_A": {
        "system_description": WUMPLE_fall_2023_Version_A,
        "mermaid_code_solution": """stateDiagram-v2
        
        [*] --> Watch : test / time=0h00m00s, alarmtime=0h00m00s, alarm=false, flashAlert=false, cdTime=0h00m00s

        state Watch {
            region Light {
                [*] --> Off
                state Off 
                Off --> On : D
                Off --> Flash : flash [flashAlert]
            
                note right of Off
                    entry / lightOff()
                end note
                
                state On
                On --> Off : D
                On --> Off : after10sec
                On --> Flash : flash [flashAlert]

                note right of On
                    entry / lightOn()
                end note
                
                state Flash
                Flash --> Off : anyButton
                
                note right of Flash
                    do / flash5sec()
                end note
                
                
            }
            region WatchMode {
                [*] --> AlarmOff
                state AlarmOff {

                    [*] --> TimeKeepingMode
                    state TimeKeepingMode {
                        
                        [*] --> IdleTimeKeeping
                        state IdleTimeKeeping
                        IdleTimeKeeping --> IdleTimeKeeping : B2sec / toggleFlashAlert()
                        IdleTimeKeeping --> IdleTimeKeeping : B / toggleAlarm()
                        IdleTimeKeeping --> AlarmMode : A
                        
                        note right of IdleTimeKeeping
                            do / displayTime()
                        end note
                        
                        state Seconds
                        Seconds --> Seconds : B / time+=1sec
                        IdleTimeKeeping --> Seconds : C / flashSeconds()
                        
                        state Minutes
                        Minutes --> Minutes : B / time+=1min
                        Seconds --> Minutes : C / flashMinutes()
                        
                        state Hours
                        Hours --> Hours : B / time+=1hr
                        Minutes --> Hours : C / flashHours()
                        Hours --> Seconds: C / flashSeconds()
                    }
                    TimeKeepingMode --> TimeKeepingMode : A
                    
                    state AlarmMode {
                        
                        [*] --> IdleAlarm
                        state IdleAlarm
                        IdleAlarm --> CountdownMode : A
                        
                        note right of IdleAlarm
                            entry / displayAlarmTime()
                        end note
                        
                        state Minutes
                        IdleAlarm --> Minutes : C / flashMinutes()
                        Minutes --> Minutes : B / alarmTime+=1min
                        
                        state Hours
                        Minutes --> Hours : C / flashHours()
                        Hours --> Hours : B / alarmTime+=1hr
                        Hours --> Minutes : C / flashMinutes()
                        
                    }
                    
                    AlarmMode --> TimeKeepingMode : A
                    
                    state CountdownMode {
                        
                        [*] --> IdleCountdown
                        state IdleCountdown
                        IdleCountdown --> Countdown : B [cdTime > 0h00m00s] / targetTime=time+cdTime
                        
                        note right of IdleCountdown
                            entry / displayCdTime()
                        end note
                        
                        state Seconds
                        IdleCountdown --> Seconds : C / flashSeconds()
                        Seconds --> Seconds : B / cdTime+=1sec
                        
                        state Minutes
                        Seconds --> Minutes : C / flashMinutes()
                        Minutes --> Minutes : B / cdTime+=1min
                        
                        state Hours
                        Minutes --> Hours : C / flashHours()
                        Hours --> Hours : B / cdTime+=1hr
                        Hours --> Minutes : C / flashMinutes()
                    }
                    CountdownMode --> CountdownMode : A

                    state Countdown
                    Countdown --> IdleCountdown : B / cdTime=targetTime-time
                    Countdown --> CountdownReached : [targetTime == time] / flash()
                    
                    note right of Countdown
                        do / displayCountdown()
                    end note
                    
                    
                    state CountdownReached
                    CountdownReached --> CountdownMode : anyButton
                    
                    note right of CountdownReached
                        do / flashZeroAndBeep5Sec()
                    end note

                    
                    state H
                }
                
                state AlarmOn
                AlarmOff --> AlarmOn : [alarm && alarmTime == time] / saveDisplay(), flash()
                AlarmOn --> AlarmOff : anyButton
                
                note right of AlarmOn
                    do / flashAlarmTimeAndBeep5Sec()
                    exit / restoreDisplay()
                end note
            }
        }
        """,
    },
    "SSC7_fall_2024_Version_A": {
        "system_description": SSC7_fall_2024_Version_A,
        "mermaid_code_solution": """stateDiagram-v2
        
        state TimeoutCountdown
        
        note right of TimeoutCountdown
            do / countFrom60()
        end note
        
        state Override
        Override --> Override : codeEntered [!codeCorrect()] / error()
        
        note right of Override
            entry / lightOn()
            exit / lightOff()
        end note
        
        state PayRequested
        
    
        [*] --> Active
        
        state Active {
            state Ready
            [*] --> Ready
            Ready --> Ready : scannedNr [!existNr()] / error()
            Ready --> Ready : productCodeEntered [!existsCode()] / error()
            Ready --> PayRequested : pay [billHasItem()] / sendPaymentRequest()
            PayRequested --> Ready : fail / error()
            PayRequested --> Ready : cancel
            PayRequested --> Ready : success / printBill(), readyForNextCustomer()
            Ready --> Override : cancelCheckout / setTypeEverything()
            Ready --> Override : removeItem [billHasItem()] / setTypeItem()
            Override --> Ready : codeEntered [codeCorrect() && isTypeItem()] / clearItem()
            Override --> Ready : codeEntered [codeCorrect() && isTypeEverything()] / clearEverything()
            
            state H
            TimeoutCountdown --> H : continue
            
            state WeighItem
            Ready --> WeighItem : productCodeEntered [existCode()]
            WeighItem --> Ready : cancel
            
            state CheckWeight
            WeighItem --> CheckWeight : weightedItem / addWeightedItem()
            Ready --> CheckWeight : scannedNr [existsNr()] / addItem()
            CheckWeight --> Ready : secWeightedItem [weightMatched()]
            CheckWeight --> Override : cancelCheckout / setTypeEverything()
            CheckWeight --> Override : secWeightedItem [!weightMatched()] / setTypeItem()
            
            state WeighBag
            Ready --> WeighBag : broughtOwnBag
            WeighBag --> Ready : secWeighedItem / addBag()
            WeighBag --> Ready : cancel
        }
        Active --> TimeoutCountdown : timeoutWarning
        TimeoutCountdown --> Active : / clearEverything(), readyForNextCustomer() 
        """,
    }
}


def get_n_shot_examples(example_names, tables):
    """ Gets the n-shot examples as a formatted string for the given example names and tables.
    
    Args:       
        example_names (list of str): The list of example names to include in the n-shot examples
        tables (list of str): The list of table names to include in the n-shot examples

    Returns:
        str: The formatted n-shot examples string for the given example names and tables.
    """
    result = ""
    for i, example in enumerate(example_names):
        if example in n_shot_examples:
            result += f"Example {i+1}:\n"
            for table in tables:
                result += f"\n{table}:\n<{table}>{n_shot_examples[example][table]}</{table}>\n"
            result += "\n"
    return result.strip()

def get_example_mermaid_code(example_name):
    """ Gets the mermaid code solution for a given example name.
    
    Args:
        example_name (str): The name of the example to retrieve the mermaid code for.
        e.g. "printer_winter_2017", "spa_manager_winter_2018", etc.
    Returns:
        str: The mermaid code solution for the given example name.
    """
    if example_name in n_shot_examples:
        return n_shot_examples[example_name]["mermaid_code_solution"]
    else:
        return None