# Color definitions using ANSI escape codes
def red: "\u001b[31m" + . + "\u001b[0m";
def yellow: "\u001b[33m" + . + "\u001b[0m";
def green: "\u001b[32m" + . + "\u001b[0m";
def blue: "\u001b[34m" + . + "\u001b[0m";
def cyan: "\u001b[36m" + . + "\u001b[0m";
def magenta: "\u001b[35m" + . + "\u001b[0m";
def bold: "\u001b[1m" + . + "\u001b[0m";
def dim: "\u001b[2m" + . + "\u001b[0m";

# Format timestamp to be more readable
def format_timestamp:
  if type == "string" then
    # Extract time portion and milliseconds
    split("T")[1] // . | 
    split("Z")[0] // . |
    split(".")[0] + "." + (split(".")[1] // "000")[0:3]
  else . end;

# Abbreviate logger names for conciseness
def abbreviate_logger:
  split(".") | 
  if length > 2 then
    [.[0:-1] | map(.[0:1]), .[-1]] | flatten | join(".")
  elif length == 2 then
    [.[0][0:1], .[1]] | join(".")
  else . | join(".") end;

# Format location (module:function:line)
def format_location:
  if .module and .function and .line then
    "\(.module):\(.function):\(.line)"
  else "" end;

# Pretty format values (handles nested objects, arrays, etc.)
def format_value:
  if type == "object" then
    to_entries |
    map("  " + .key + ": " + (.value | format_value)) |
    join("\n") |
    "\n" + .
  elif type == "array" then
    if length == 0 then "[]"
    else
      map(format_value) |
      to_entries |
      map("  [" + (.key | tostring) + "]: " + .value) |
      join("\n") |
      "\n" + .
    end
  elif type == "string" then
    if test("^\\{.*\\}$|^\\[.*\\]$") then
      # Looks like JSON, try to parse and format
      try (fromjson | format_value) catch .
    else . end
  else tostring end;

# Format extra fields with better nested object support
def format_extras:
  if . then
    to_entries |
    map(
      .key as $k |
      .value as $v |
      dim + " " + $k + "=" +
      (if ($v | type) == "object" or ($v | type) == "array" then
         "\n" + ($v | format_value | dim)
       else
         $v | tostring | dim
       end)
    ) |
    join("")
  else "" end;

# Detect special message types for highlighting
def detect_special_type:
  if test("WebSocket|websocket|WS") then "websocket"
  elif test("consciousness|Consciousness") then "consciousness"
  elif test("✅|✓|Success|initialized successfully") then "success"
  elif test("🚀|🎉|Starting|started") then "emphasis"
  elif test("⚠️|Warning") then "warning"
  elif test("❌|Error|Failed") then "error"
  else "normal" end;

# Apply special highlighting to message
def highlight_message:
  . as $msg |
  ($msg | detect_special_type) as $type |
  if $type == "websocket" then cyan
  elif $type == "consciousness" then magenta
  elif $type == "success" then green
  elif $type == "emphasis" then bold
  elif $type == "warning" then yellow
  elif $type == "error" then red
  else
    # Check if message looks like JSON and try to format it
    if test("^\\{.*\\}$|^\\[.*\\]$") then
      try (fromjson | format_value) catch .
    else . end
  end;

# Main formatting function
def format_log:
  # Determine level color
  (.level | ascii_downcase) as $level |
  (if $level == "debug" then "\u001b[2m"
   elif $level == "info" then "\u001b[34m"
   elif $level == "warning" or $level == "warn" then "\u001b[33m"
   elif $level == "error" then "\u001b[31m"
   elif $level == "critical" then "\u001b[1;31m"
   else "" end) as $level_color |
  
  # Format level (fixed width)
  ($level | ascii_upcase | .[0:5] | . + "     "[0:(5 - length)]) as $level_display |
  
  # Apply color to level display
  ($level_color + $level_display + "\u001b[0m") as $colored_level |
  
  # Build output string
  [
    # Timestamp
    ((.timestamp | format_timestamp) | dim),
    
    # Level
    $colored_level,
    
    # Logger (abbreviated)
    ((.logger | abbreviate_logger) | cyan),
    
    # Message (with special highlighting)
    (.message | highlight_message),
    
    # Location (if available)
    (if .module then
      ("[" + (.module + ":" + .function + ":" + (.line | tostring)) + "]" | dim)
    else "" end),
    
    # Thread (if not MainThread)
    (if .thread and .thread != "MainThread" then
      ("(" + .thread + ")" | dim)
    else "" end),
    
    # Correlation/Trace IDs (if present)
    (if .correlation_id then
      (" corr:" + .correlation_id | dim)
    else "" end),
    
    (if .trace_id then
      (" trace:" + .trace_id | dim)
    else "" end),
    
    # Extra fields
    (if .extra then
      .extra | format_extras
    else "" end)
  ] |
  map(select(. != "")) |
  join(" ");

# Main entry point
if type == "object" then
  format_log
else
  # Handle non-JSON lines (like plain text logs)
  .
end
