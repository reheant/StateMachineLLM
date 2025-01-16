from state_machine_descriptions import *

n_shot_examples = {
    "printer_winter_2017": {
        "system_description": printer_winter_2017,
        "umple_code_solution": '''class Printer{
 sm {
   Off {on -> On;}
   On{
     off -> Off;
     Idle {
       login(cardID) [!idAuthorized(cardID)] -> Idle;
       login(cardID) [idAuthorized(cardID)] / {action="none";} -> Ready;
     }
     
     Ready{
       logoff -> Idle;
       start [action=="scan" && !originalLoaded()] -> Ready;
       start [action=="print" && !documentInQueue()] -> Ready;
       
       scan /{action="scan";} -> Ready;
       
       print /{action="print";} -> Ready;
       
       start [action=="scan" && originalLoaded()] -> ScanAndEmail;
       
       start [action=="print" && documentInQueue()] -> Print;
     }
     
     Busy{
      ScanAndEmail{
        
      }
       
       Print{
         outOfPaper -> Suspended;
       }
       
       jam -> Suspended;
       
       stop -> Ready;
       done -> Ready;
     }
     
     Suspended{
      cancel -> Ready;
       
       resume -> Busy.H;
     }
   }
 }
}'''
    },
    "spa_manager_winter_2018": {
        "system_description": spa_manager_winter_2018,
        "umple_code_solution":'''class SpaManager{
 sm {
  SpaManager{
    Jacuzzi{
    	Off{
       		on -> Jacuzzi.On;   
        }
      
      On{
        off -> Jacuzzi.Off;
        
        Level1{
         up -> Level2; 
        }
        
        Level2{
         up -> Level3;
         down -> Level1;
        }
        
        Level3{
         down -> Level2; 
        }
        
        pause -> Paused;
        
        setPattern(PatternType type) -> Jacuzzi.On.H;
      }
      
      Paused{
       off -> Jacuzzi.Off;
        
        after2min -> Jacuzzi.On.H;
      }
    }
    ||
    Sauna{
     Off{
       on -> Sauna.On;
     }
      
      On{
        off -> Sauna.Off;
        
        Heater{
        	Heat{
              [temp>=90] -> Heater.Idle;
            }
          
          Idle{
       		[temp < 85] -> Heat;     
          }
        }
        ||
          Fan{
          Off{
           [humidity > 0.40 && exceedTime>3] -> Fan.On; 
          }
          
          On{
           after5min -> Fan.Off; 
          }
        }
        ||
          Water{
          Idle{
           	 disperse [humidity<0.04 && !Fan.On && timeSinceLast>15] -> Water.Idle;
          }
        }
      }
    }
  }
 }
}'''
    },
    "dishwasher_winter_2019": {
        "system_description": dishwasher_winter_2019,
        "umple_code_solution":'''class Dishwasher {
  status {
    state0 {
      doorState {
        Closed {
          open -> Open;
          lock -> Locked;
        }
        Open {
          close -> Closed;
        }
        Locked {
          unlock -> Closed;
        }
      }
      ||
      washingState {
        Idle {
          selectProgram(n) [n >= 1] -> /{r=n;} Idle;
          toggleDryingTime -> /{if (dT=20) dT=40; else dT = 20} Idle;
          start [door.isClosed()] -> /{door.lock();c=1;} Cleaning;
        }
        Suspended {
          close -> Drying;
          after(5) -> Idle;
        }
        Drying {
          extendDryingTime -> /{dT=40;} Drying;
          open -> Suspended;
          after(dT) -> Idle;
        }
        Cleaning {
          Intake {
            entry/{} -> Washing;
          }
          Washing {
            after(10) -> Drain;
          }
          Drain {
            [c < r] ->/{c++;} Intake;
            [c >= r] -> FinalCleaning;
          }
          FinalCleaning {
            entry/{door.unlock();} -> Drying;
          }
          toggleDryingTime -> /{if (dT=20) dT=40; else dT = 20} Cleaning.H;
        }
      }
    }
  }
}'''
    },
    "chess_clock_fall_2019": {
        "system_description": chess_clock_fall_2019,
        "umple_code_solution":'''class ChessClock {
  status {
    Off {
      onOff -> On;
    }
    On {
      GameSetup {
        TimingSelection {
          plus -> /{incrTimingProgram();} TimingSelection;
          minus -> /{decrTimingProgram();} TimingSelection;
        }
        ||
        WhiteKingStatus {
          WhiteKingOnLeft {
            flip -> WhiteKingOnRight;
          }
          WhiteKingOnRight {
            flip -> WhiteKingOnLeft;
          }
        }
      select -> ReadyToStart;
      }
      ReadyToStart{
        startStop -> GameRunning;
      }
      GameRunning {
        WhiteClockRunning {
          after(1) [wc > 0] -> /{decrTimer(wc);} WhiteClockRunning;
          after(1) [wc == 0] -> /{flashFlag(white);} GameFinished;
          flip -> BlackClockRunning;
          entry / {startTimer(wc);}
          exit / {stopTimer(wc);}
        }
        BlackClockRunning {
          after(1) [bc > 0] -> /{decrTimer(bc);} BlackClockRunning;
          after(1) [bc == 0] -> /{flashFlag(black);} GameFinished;
          flip -> WhiteClockRunning;
          entry / {startTimer(bc);}
          exit / {stopTimer(bc);}
        }
      startStop -> GamePaused;
      }
      GamePaused {
        startStop -> GameRunning.H;
      }
      GameFinished {
      }
    onOff -> Off;
    }
  }    
}'''
    },
    "thermomix_fall_2021": {
        "system_description": thermomix_fall_2021,
        "umple_code_solution": '''class Thermomix {
  sm {
    TransportationMode {
    	selectorPressed -> On;
    }
    PreparingOff {
     	selectorReleased -> On.H ;
      	after5sec -> Off;
    }
    Off {
      	selectorPressed -> On;
    }
    On {
      	selectorHeld -> PreparingOff;
      	bowlRemoved -> On;
		Home {
          after14min30sec -> PreparingShutdown;
          start [!bowlRemoved()] / {action=setIngredients();} -> PromptToAdd;
        }
      	PreparingShutdown {
        	cancel -> Home;
          	after30sec -> Off;
        }
      	PromptToAdd {
			next[weightCorrect() && moreIngredientsRequired] / {action=setIngredients;} -> PromptToAdd;
          	next[weightCorrect() && !moreIngredientsRequired] / {action=setChoppingSpeedAndTime();} -> Chop;
        }
      	Chop {
          next [choppingTimeDone && moreIngredientsRequired()] / {action=setIngredients();} -> PromptToAdd;
          next [choppingTimeDone && !moreIngredientsRequired()] / {action=setCookingSpeedAndTime();} -> Cook;
        }
      	Cook {
          afterChoppingTime [moreIngredientsRequired] / {action=setIngredients();} -> PromptToAdd;
          afterCookingTime [!moreIngredientsRequired] -> Ready;
        }
      	Ready {
        	after14min30sec -> PreparingShutdown; 
        }
    }
  }
}'''
    },
    "ATAS_fall_2022": {
        "system_description": ATAS_fall_2022,
        "umple_code_solution": '''class AdvancedTrainAutomationSystem {
  sm {
    Scheduled {
      atBeginningStopDuration / {action=p0n; setCs;} -> Active;
    }
    
    Arrived {
      
    }
    
    Active {
      TrainMovement {
        emergency / {action=estop} -> Emergency;
        AtStation {
          	afterStopDuration [!isLastStop()] -> StopNotRequired;
          	afterStopDuration [isLastStop()] / {action=pOff} -> Arrived;
        }
        
        StopNotRequired {
          enteringSegment [isStationSegment() && !stopRequired()] -> StopNotRequired;
          enteringSegment [isRegularSegment()] -> StopNotRequired;
          enteringSegment [isTrafficLightSegment() && !isRed()] -> StopNotRequired;
          enteringSegment [isTrafficLightSegment() && isRed()] -> ApproachingRedLight;
          enteringSegment [isStationSegment() && stopRequired()] -> ApproachingStation;
        }
        
        ApproachingRedLight {
         	 stopped -> AtRedTrafficLight;
        }
        
        AtRedTrafficLight {
         	 green -> StopNotRequired;
        }
        
        ApproachingStation {
         	 stopped -> AtStation;
        }
        
      } || 
      SDS {
		SDSActive {
         	after1sec [hasSegmentChanged()] / {action=setCs; enteringSegment();} -> SDSActive;
          
          	after1sec [!hasSegmentChanged()] -> SDSActive;
        }
      } ||
        MDS { 
        	Stopped {
              after1sec [speed == 0] -> Stopped;
              after1sec [speed > 0] -> Moving;
            }
        
        	Moving {
              after1sec [speed > 0] -> Moving;
              after1sec [speed == 0] / {action=stopped()} -> Stopped;
            }

      } || 
        ODS { 
        	ODSActive {
             	after1sec [!obstacleDetected()] -> ODSActive;
              	after1sec [obstacleDetected()] / {action=emergency();} -> ODSActive;
            }
      	}
      
      Emergency {
        clear -> TrainMovement.H;
      }
    }
  }
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
