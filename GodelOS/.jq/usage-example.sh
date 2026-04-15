#!/bin/bash

# Example usage of the colour-logs.jq filter

# For streaming logs in real-time
echo "# Stream backend logs with color:"
echo "tail -f backend.log | jq -R 'try fromjson' | jq -r -f .jq/colour-logs.jq"
echo ""

# For viewing existing log file
echo "# View existing log file with color:"
echo "cat backend.log | jq -R 'try fromjson' | jq -r -f .jq/colour-logs.jq"
echo ""

# For filtering by log level
echo "# Filter only ERROR and WARNING logs:"
echo "cat backend.log | jq -R 'try fromjson | select(.level == \"ERROR\" or .level == \"WARNING\")' | jq -r -f .jq/colour-logs.jq"
echo ""

# For filtering by component
echo "# Filter by specific component:"
echo "cat backend.log | jq -R 'try fromjson | select(.component == \"cognitive_manager\")' | jq -r -f .jq/colour-logs.jq"
echo ""

# For consciousness-related logs
echo "# Show only consciousness assessment logs:"
echo "cat backend.log | jq -R 'try fromjson | select(.cognitive_state != null)' | jq -r -f .jq/colour-logs.jq"
