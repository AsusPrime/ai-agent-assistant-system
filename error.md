> what you see
[Plan] 1 step(s):
  1. run_command | ls | {'args': '[]'}
  Reasoning: Listing the contents of the current directory to inform the user what is there.
Execute plan? [y/N]: y
[stderr] ls: []: No such file or directory

[Error] Step 'ls' failed (rc=1). Stopping.
[Correction] Asking LLM for a corrected plan...
[Plan] 1 step(s):
  1. run_command | ls | {'args': 0}
  Reasoning: The previous 'ls' command failed because an empty array string "[]" was passed as a literal argument. I will now run 'ls' with no arguments to correctly list the directory contents.
Execute corrected plan? [y/N]: y
[stderr] 'int' object is not iterable
[Error] Step 'ls' failed (rc=1). Stopping.