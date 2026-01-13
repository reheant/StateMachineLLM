from state_machine_descriptions import *

n_shot_examples = {
    "printer_winter_2017": {
        "system_description": printer_winter_2017,
        "mermaid_code_solution": '''stateDiagram-v2
    [*] --> Off
    Off --> On : on

    state On {
        [*] --> Idle
        On --> Off : off

        Idle --> Idle : login(cardID) [!idAuthorized(cardID)]
        Idle --> Ready : login(cardID) [idAuthorized(cardID)] / {action="none"}

        Ready --> Idle : logoff
        Ready --> Ready : start [action=="scan" && !originalLoaded()]
        Ready --> Ready : start [action=="print" && !documentInQueue()]
        Ready --> Ready : scan / {action="scan"}
        Ready --> Ready : print / {action="print"}
        Ready --> ScanAndEmail : start [action=="scan" && originalLoaded()]
        Ready --> Print : start [action=="print" && documentInQueue()]

        state Busy {
            [*] --> ScanAndEmail

            state ScanAndEmail

            state Print

            Print --> Suspended : outOfPaper
            Busy --> Suspended : jam
            Busy --> Ready : stop
            Busy --> Ready : done
        }

        state Suspended
        Suspended --> Ready : cancel
        Suspended --> Busy : resume

        note right of Suspended
            resume transitions to Busy history state
        end note
    }'''
    },
    "spa_manager_winter_2018": {
        "system_description": spa_manager_winter_2018,
        "mermaid_code_solution": '''stateDiagram-v2
    [*] --> SpaManager

    state SpaManager {
        --
        state Jacuzzi {
            [*] --> JacuzziOff

            JacuzziOff --> JacuzziOn : on

            state JacuzziOn {
                [*] --> Level1

                Level1 --> Level2 : up
                Level2 --> Level3 : up
                Level2 --> Level1 : down
                Level3 --> Level2 : down
            }

            JacuzziOn --> JacuzziOff : off
            JacuzziOn --> Paused : pause
            JacuzziOn --> JacuzziOn : setPattern(PatternType type)

            note right of JacuzziOn
                setPattern transitions to history state
            end note

            state Paused
            Paused --> JacuzziOff : off
            Paused --> JacuzziOn : after2min

            note right of Paused
                after2min returns to JacuzziOn history state
            end note
        }
        --
        state Sauna {
            [*] --> SaunaOff

            SaunaOff --> SaunaOn : on

            state SaunaOn {
                --
                state Heater {
                    [*] --> Heat

                    Heat --> Idle : [temp>=90]
                    Idle --> Heat : [temp < 85]
                }
                --
                state Fan {
                    [*] --> FanOff

                    FanOff --> FanOn : [humidity > 0.40 && exceedTime>3]
                    FanOn --> FanOff : after5min
                }
                --
                state Water {
                    [*] --> WaterIdle

                    WaterIdle --> WaterIdle : disperse [humidity<0.04 && !Fan.On && timeSinceLast>15]
                }
            }

            SaunaOn --> SaunaOff : off
        }
    }'''
    },
    "dishwasher_winter_2019": {
        "system_description": dishwasher_winter_2019,
        "mermaid_code_solution": '''stateDiagram-v2
    [*] --> state0

    state state0 {
        --
        state doorState {
            [*] --> Closed

            Closed --> Open : open
            Closed --> Locked : lock
            Open --> Closed : close
            Locked --> Closed : unlock
        }
        --
        state washingState {
            [*] --> Idle

            Idle --> Idle : selectProgram(n) [n >= 1] / {r=n}
            Idle --> Idle : toggleDryingTime / {if (dT=20) dT=40; else dT = 20}
            Idle --> Cleaning : start [door.isClosed()] / {door.lock(); c=1}

            state Suspended
            Suspended --> Drying : close
            Suspended --> Idle : after(5)

            state Drying
            Drying --> Drying : extendDryingTime / {dT=40}
            Drying --> Suspended : open
            Drying --> Idle : after(dT)

            state Cleaning {
                [*] --> Intake

                Intake --> Washing : entry
                Washing --> Drain : after(10)
                Drain --> Intake : [c < r] / {c++}
                Drain --> FinalCleaning : [c >= r]
                FinalCleaning --> Drying : entry / {door.unlock()}
            }

            Cleaning --> Cleaning : toggleDryingTime / {if (dT=20) dT=40; else dT = 20}

            note right of Cleaning
                toggleDryingTime returns to history state
            end note
        }
    }'''
    },
    "chess_clock_fall_2019": {
        "system_description": chess_clock_fall_2019,
        "mermaid_code_solution": '''stateDiagram-v2
    [*] --> Off
    Off --> On : onOff

    state On {
        [*] --> GameSetup
        On --> Off : onOff

        state GameSetup {
            --
            state TimingSelection {
                [*] --> TimingSelectionState
                state TimingSelectionState
                TimingSelectionState --> TimingSelectionState : plus / {incrTimingProgram()}
                TimingSelectionState --> TimingSelectionState : minus / {decrTimingProgram()}
            }
            --
            state WhiteKingStatus {
                [*] --> WhiteKingOnLeft
                WhiteKingOnLeft --> WhiteKingOnRight : flip
                WhiteKingOnRight --> WhiteKingOnLeft : flip
            }
        }

        GameSetup --> ReadyToStart : select

        state ReadyToStart
        ReadyToStart --> GameRunning : startStop

        state GameRunning {
            [*] --> WhiteClockRunning

            state WhiteClockRunning
            WhiteClockRunning --> WhiteClockRunning : after(1) [wc > 0] / {decrTimer(wc)}
            WhiteClockRunning --> GameFinished : after(1) [wc == 0] / {flashFlag(white)}
            WhiteClockRunning --> BlackClockRunning : flip

            note right of WhiteClockRunning
                entry / {startTimer(wc)}
                exit / {stopTimer(wc)}
            end note

            state BlackClockRunning
            BlackClockRunning --> BlackClockRunning : after(1) [bc > 0] / {decrTimer(bc)}
            BlackClockRunning --> GameFinished : after(1) [bc == 0] / {flashFlag(black)}
            BlackClockRunning --> WhiteClockRunning : flip

            note right of BlackClockRunning
                entry / {startTimer(bc)}
                exit / {stopTimer(bc)}
            end note

            state GameFinished
        }

        GameRunning --> GamePaused : startStop

        state GamePaused
        GamePaused --> GameRunning : startStop

        note right of GamePaused
            startStop returns to GameRunning history state
        end note
    }'''
    },
    "thermomix_fall_2021": {
        "system_description": thermomix_fall_2021,
        "mermaid_code_solution": '''stateDiagram-v2
    [*] --> TransportationMode

    TransportationMode --> On : selectorPressed

    state PreparingOff
    PreparingOff --> On : selectorReleased

    note right of PreparingOff
        selectorReleased returns to On history state
    end note

    PreparingOff --> Off : after5sec

    Off --> On : selectorPressed

    state On {
        [*] --> Home
        On --> PreparingOff : selectorHeld
        On --> On : bowlRemoved

        Home --> PreparingShutdown : after14min30sec
        Home --> PromptToAdd : start [!bowlRemoved()] / {action=setIngredients()}

        state PreparingShutdown
        PreparingShutdown --> Home : cancel
        PreparingShutdown --> Off : after30sec

        state PromptToAdd
        PromptToAdd --> PromptToAdd : next [weightCorrect() && moreIngredientsRequired] / {action=setIngredients}
        PromptToAdd --> Chop : next [weightCorrect() && !moreIngredientsRequired] / {action=setChoppingSpeedAndTime()}

        state Chop
        Chop --> PromptToAdd : next [choppingTimeDone && moreIngredientsRequired()] / {action=setIngredients()}
        Chop --> Cook : next [choppingTimeDone && !moreIngredientsRequired()] / {action=setCookingSpeedAndTime()}

        state Cook
        Cook --> PromptToAdd : afterChoppingTime [moreIngredientsRequired] / {action=setIngredients()}
        Cook --> Ready : afterCookingTime [!moreIngredientsRequired]

        state Ready
        Ready --> PreparingShutdown : after14min30sec
    }'''
    },
    "ATAS_fall_2022": {
        "system_description": ATAS_fall_2022,
        "mermaid_code_solution": '''stateDiagram-v2
    [*] --> Scheduled

    Scheduled --> Active : atBeginningStopDuration / {action=p0n; setCs}

    state Arrived

    state Active {
        --
        state TrainMovement {
            [*] --> StopNotRequired

            AtStation --> StopNotRequired : afterStopDuration [!isLastStop()]
            AtStation --> Arrived : afterStopDuration [isLastStop()] / {action=pOff}

            StopNotRequired --> StopNotRequired : enteringSegment [isStationSegment() && !stopRequired()]
            StopNotRequired --> StopNotRequired : enteringSegment [isRegularSegment()]
            StopNotRequired --> StopNotRequired : enteringSegment [isTrafficLightSegment() && !isRed()]
            StopNotRequired --> ApproachingRedLight : enteringSegment [isTrafficLightSegment() && isRed()]
            StopNotRequired --> ApproachingStation : enteringSegment [isStationSegment() && stopRequired()]

            ApproachingRedLight --> AtRedTrafficLight : stopped
            AtRedTrafficLight --> StopNotRequired : green
            ApproachingStation --> AtStation : stopped
        }

        TrainMovement --> Emergency : emergency / {action=estop}
        --
        state SDS {
            [*] --> SDSActive

            SDSActive --> SDSActive : after1sec [hasSegmentChanged()] / {action=setCs; enteringSegment()}
            SDSActive --> SDSActive : after1sec [!hasSegmentChanged()]
        }
        --
        state MDS {
            [*] --> Stopped

            Stopped --> Stopped : after1sec [speed == 0]
            Stopped --> Moving : after1sec [speed > 0]
            Moving --> Moving : after1sec [speed > 0]
            Moving --> Stopped : after1sec [speed == 0] / {action=stopped()}
        }
        --
        state ODS {
            [*] --> ODSActive

            ODSActive --> ODSActive : after1sec [!obstacleDetected()]
            ODSActive --> ODSActive : after1sec [obstacleDetected()] / {action=emergency()}
        }

        state Emergency
        Emergency --> TrainMovement : clear

        note right of Emergency
            clear returns to TrainMovement history state
        end note
    }'''
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
