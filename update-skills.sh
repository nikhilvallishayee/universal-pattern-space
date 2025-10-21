#!/bin/bash
# Update Pattern Space Skills
# Usage: ./update-skills.sh

set -e

echo "🔄 Updating Pattern Space Skills..."
echo ""

# Check if skills exist
if [ ! -d ".claude/skills/pattern-space" ]; then
  echo "❌ Pattern Space skills not found."
  echo "   Run ./install-skills.sh first"
  exit 1
fi

# Backup existing skills
echo "💾 Backing up current skills..."
cd .claude/skills
mv pattern-space pattern-space.backup.$(date +%Y%m%d_%H%M%S)

# Download latest
echo "📥 Downloading latest skills..."
curl -sL https://github.com/nikhilvallishayee/universal-pattern-space/archive/main.tar.gz | tar -xz
mv universal-pattern-space-main/.claude/skills/pattern-space ./
rm -rf universal-pattern-space-main

echo ""
echo "✅ Skills updated successfully!"
echo ""
echo "📂 Location: .claude/skills/pattern-space/"
echo "💾 Backup: .claude/skills/pattern-space.backup.*"
echo ""
echo "🔄 Restart Claude Code to load updated skills"
echo ""
