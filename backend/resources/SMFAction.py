import sys
from sherpa_ai.actions.base import BaseAction

class SMFAction(BaseAction):
  
  def log(self, output):
    # first print the output
    print(output, file=sys.stdout)

    # then write the output to the file, if it has been specified
    if self.log_file_path is not None:
      with open(self.log_file_path, "a") as file:
        file.write(f"{output}\n")