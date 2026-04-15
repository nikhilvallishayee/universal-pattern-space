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
    "{\n" + (
      to_entries |
      map("  " + .key + ": " + (.value | format_value)) |
      join(",\n")
    ) + "\n}"
  elif type == "array" then
    if length == 0 then "[]"
    else
      "[\n" + (
        map("  " + format_value) |
        join(",\n")
      ) + "\n]"
    end
  else tostring end;

# Format extra fields
def format_extras:
  if . then
    to_entries |
    map(dim + " " + .key + "=" + (.value | tostring)) |
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

# Indentation helper (two spaces per level)
def indent($n): ([range(0; $n) | "  "] | join(""));

# Pretty-print Python-like dicts/lists by inserting newlines/indentation
# Note: Heuristic parser – assumes no escaped quotes inside strings.
def pretty_python_braces:
  reduce (split("")[]) as $c (
    {out:"", depth:0, in_str:false, quote:""};
    if .in_str then
      if $c == .quote then
        .in_str = false | .out = (.out + $c)
      else
        .out = (.out + $c)
      end
    else
      if ($c == "'" or $c == "\"") then
        .in_str = true | .quote = $c | .out = (.out + $c)
      elif ($c == "{" or $c == "[") then
        (.out = (.out + ($c + "\n" + indent(.depth + 1)))) | (.depth += 1)
      elif ($c == "}" or $c == "]") then
        (.depth -= 1) | (.out = (.out + ("\n" + indent(.depth) + $c)))
      elif $c == "," then
        .out = (.out + (",\n" + indent(.depth)))
      elif $c == ":" then
        # Normalize to a single space after colon
        .out = (.out + ": ")
      else
        .out = (.out + $c)
      end
    end
  ) | .out
  # Normalize any accidental double spaces after colon
  | gsub(":  +"; ": ")
  # Inline empty dicts and lists
  | gsub("\\{\\n\\s*\\}"; "{}")
  | gsub("\\[\\n\\s*\\]"; "[]")
  # Remove empty blank lines
  | gsub("\\n[ \t]*\\n+"; "\n");

# Syntax highlight tokens in Python-like output
def colorize_python_like:
  .
  # Numbers (cyan)
  | gsub("(?<num>-?[0-9]+(\\.[0-9]+)?([eE][+-]?[0-9]+)?)"; "\(.num | cyan)")
  # Booleans/None (magenta)
  | gsub("(?<bool>\\b(True|False|None)\\b)"; "\(.bool | magenta)")
  # Strings (single or double quoted) (green)
  | gsub("(?<str>'[^']*'|\"[^\"]*\")"; "\(.str | green)");

# Pretty-print and colorize JSON values (objects/arrays/scalars)
def pretty_json_color($lvl):
  if type == "object" then
    "{\n" + (
      to_entries |
      map(indent($lvl) + (.key | tojson | cyan) + ": " + (.value | pretty_json_color($lvl+1))) |
      join(",\n")
    ) + "\n" + indent($lvl-1) + "}"
  elif type == "array" then
    if length == 0 then "[]" else
      "[\n" + (map(indent($lvl) + (.| pretty_json_color($lvl+1))) | join(",\n")) + "\n" + indent($lvl-1) + "]"
    end
  elif type == "string" then (. | tojson | green)
  elif type == "number" then (tostring | cyan)
  elif type == "boolean" then (tostring | magenta)
  elif . == null then ("null" | magenta)
  else tostring end;

# Fallback: colorize a JSON-like string without parsing (best-effort)
def colorize_jsonish_string:
  .
  | gsub(":\\s*"; ": ")
  | gsub("(?<key>\"[^\"]+\")\\s*:"; "\\(.key | cyan):")
  | gsub("(?<str>\"[^\"]*\")"; "\\(.str | green)")
  | gsub("\\b(?<bool>true|false|null)\\b"; "\\(.bool | magenta)")
  | gsub("(?<num>-?[0-9]+(\\.[0-9]+)?)"; "\\(.num | cyan)");

  # Colorize plain DEBUG PING/PONG lines
def colorize_plain_debug:
  . as $line |
  if ($line | ascii_downcase | test("^debug:.*text [\"']\\{")) then
    # DEBUG TEXT with JSON payload inside single quotes
    try (
      $line | capture("^(?<label>DEBUG:)[[:space:]]+(?<dir><|>)[[:space:]]*[Tt][Ee][Xx][Tt][[:space:]]*[\"'](?<payload>[^\"']*)[\"'](?<rest>.*)$") as $m |
      (
        ("DEBUG" | cyan) + ": " +
        (if $m.dir == "<" then ("<" | green) else (">" | yellow) end) + " TEXT" +
        "\n" + (
          try ($m.payload | fromjson | pretty_json_color(1)) catch ($m.payload | colorize_jsonish_string)
        ) +
        (if ($m.rest | length) > 0 then " " + ($m.rest | dim) else "" end)
      )
    ) catch (
      # Fallback to simple coloring if capture/fromjson fails
      $line
      | sub("^DEBUG:"; ("\u001b[36m" + "DEBUG" + "\u001b[0m" + ":"))
    )
  else
    $line
    | sub("^DEBUG:"; ("\u001b[36m" + "DEBUG" + "\u001b[0m" + ":"))
    | gsub("> PING"; ("\u001b[33m> PING\u001b[0m"))
    | gsub("< PONG"; ("\u001b[32m< PONG\u001b[0m"))
    | gsub("% sending keepalive ping"; ("\u001b[33m% sending keepalive ping\u001b[0m"))
    | gsub("% received keepalive pong"; ("\u001b[32m% received keepalive pong\u001b[0m"))
  end;

# Colorize plain INFO HTTP access lines
def colorize_plain_info:
  . as $line |
  try (
    $line | capture("^(?<label>INFO:)[[:space:]]+(?<ip>[0-9]{1,3}(?:\\.[0-9]{1,3}){3}:[0-9]{2,5})[[:space:]]+-[[:space:]]+\"(?<method>GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)[[:space:]]+(?<path>[^ \"\\r\\n]+)[[:space:]]+(?<http>HTTP/[0-9]+\\.[0-9]+)\"[[:space:]]+(?<code>[0-9]{3})[[:space:]]+(?<msg>.*)$") as $m |
    (
      ("INFO" | blue) + ": " +
      ($m.ip | dim) + " - \"" +
      ($m.method | cyan) + " " +
      ($m.path | bold) + " " +
      ($m.http | dim) + "\" " +
      ( ($m.code | tonumber) as $c | if $c>=200 and $c<300 then ($m.code | green)
        elif $c>=300 and $c<400 then ($m.code | yellow)
        else ($m.code | red) end ) + " " +
      (if $m.msg == "OK" then ($m.msg | green) else $m.msg end)
    )
  ) catch $line;

# Simple readability improvement for GödelOS logs
def format_godelos_readable:
  . as $msg |
  if test("UnifiedConsciousnessState") then
    # Add line breaks between major sections
  ($msg |
    sub(", phenomenal_experience="; ",\n  phenomenal_experience="; "g") |
    sub(", information_integration="; ",\n  information_integration="; "g") |
    sub(", global_workspace="; ",\n  global_workspace="; "g") |
    sub(", metacognitive_state="; ",\n  metacognitive_state="; "g") |
    sub(", intentional_layer="; ",\n  intentional_layer="; "g") |
    sub(", creative_synthesis="; ",\n  creative_synthesis="; "g") |
    sub(", embodied_cognition="; ",\n  embodied_cognition="; "g") |
    sub(", timestamp="; ",\n  timestamp="; "g") |
    sub(", consciousness_score="; ",\n  consciousness_score="; "g") |
  sub(", emergence_level="; ",\n  emergence_level="; "g"))
  | (
      # Scope pretty-printing to UCS payload: split prefix and payload
      (index("{'cognitive_state':") // 0) as $pstart |
      if $pstart > 0 then
        .[0:$pstart] as $prefix | .[$pstart:] as $payload |
        ($payload | pretty_python_braces | colorize_python_like) as $pp |
        $prefix + $pp
      else
        pretty_python_braces | colorize_python_like
      end
    )
  else .
  end;

# Extract and format JSON/Python dict from within text messages
def format_json_in_message:
  . as $msg |
  if test("UnifiedConsciousnessState") then
    # Apply readability improvements
    $msg | format_godelos_readable
  elif test("\\{.*\\}") then
    # For regular JSON/dicts
    (index("{") // 0) as $start |
    ($msg[$start:]) as $json_candidate |
    try (
      $json_candidate | fromjson | format_value |
      $msg[0:$start] + "\n" + .
    ) catch $msg
  else .
  end;

# Apply special highlighting to message
def highlight_message:
  . as $msg |
  # Determine type for coloring, but always format first
  ($msg | detect_special_type) as $type |
  ($msg | format_json_in_message) as $formatted |
  # Plain text DEBUG ping/pong lines
  if ($msg | type == "string") and ($msg | test("^DEBUG:")) then
    $msg | colorize_plain_debug
  elif ($msg | type == "string") and ($msg | test("^INFO:")) then
    $msg | colorize_plain_info
  else
  if $type == "websocket" then $formatted | cyan
  elif $type == "consciousness" then $formatted | magenta
  elif $type == "success" then $formatted | green
  elif $type == "emphasis" then $formatted | bold
  elif $type == "warning" then $formatted | yellow
  elif $type == "error" then $formatted | red
  else $formatted end
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
    
  # Logger (full)
  (.logger | cyan),
    
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
      " extra=" + (.extra | tostring)
    else "" end)
  ] |
  map(select(. != "")) |
  join(" ");

# Main entry point: handle both JSON and raw text lines
if type == "string" then
  # Parse only if the line looks like JSON; otherwise treat as plain text
  if test("^\\s*[{\\[]") then
    try (fromjson | format_log) catch (.| highlight_message)
  else
    . | highlight_message
  end
elif type == "object" then
  format_log
else
  .
end
