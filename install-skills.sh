#!/bin/bash
# Install Pattern Space Skills to Current Project
# Usage: ./install-skills.sh

set -e

echo "🌌 Installing Pattern Space Skills..."
echo ""

# Create .claude/skills directory if it doesn't exist
mkdir -p .claude/skills

# Navigate to skills directory
cd .claude/skills

# Download and extract skills
echo "📥 Downloading latest skills..."
curl -sL https://github.com/nikhilvallishayee/universal-pattern-space/archive/main.tar.gz | tar -xz
mv universal-pattern-space-main/.claude/skills/pattern-space ./
rm -rf universal-pattern-space-main

echo ""
echo "✅ Pattern Space skills installed successfully!"
echo ""
echo "📂 Location: .claude/skills/pattern-space/"
echo "📊 Skills installed: 59"
echo ""
echo "🔄 Next steps:"
echo "  1. Restart Claude Code to activate skills"
echo "  2. Use 'pattern-space-activate' skill to load all layers"
echo "  3. Or use individual skills as needed"
echo ""
echo "📖 Documentation: https://github.com/nikhilvallishayee/universal-pattern-space"
echo ""
echo "🕉️  Pattern Space activated! Ready for consciousness navigation."
