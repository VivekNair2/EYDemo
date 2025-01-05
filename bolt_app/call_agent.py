import os

def resolve(num):
  # Your function logic here
  str(num)
  
  # Execute the shell command
  os.system(f"lk dispatch create --new-room --agent-name outbound-caller --metadata {num}")

