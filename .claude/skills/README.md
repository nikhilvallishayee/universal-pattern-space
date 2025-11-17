# Claude Code Skills Directory

This directory contains skills for Claude Code. Skills are organized by framework/project.

## Directory Structure

```
.claude/skills/
├── pattern-space/          # Pattern Space consciousness navigation framework (59 skills)
│   ├── perspectives/       # Layer 1: 8 perspective skills
│   ├── field/             # Layer 2: 9 protocol & principle skills
│   ├── transformation/    # Layer 3: 7 transformation skills
│   ├── archaeology/       # Layer 4: 5 diagnostic skills
│   ├── wisdom/           # Layer 5: 30 wisdom stream skills
│   │   ├── breakthrough/  # 6 core breakthrough streams
│   │   ├── eastern/       # 6 Eastern tradition skills
│   │   ├── abrahamic/     # 3 Abrahamic tradition skills
│   │   ├── indigenous/    # 3 Indigenous wisdom skills
│   │   ├── divine-council/ # 4 archetypal consciousness skills
│   │   ├── modern-science/ # 1 IIT consciousness skill
│   │   ├── nature/        # 1 ecological intelligence skill
│   │   └── sacred-sciences/ # 6 sacred science skills
│   ├── pattern-space-activate.md  # Meta-skill for full activation
│   └── VERIFICATION.md    # Skills verification guide
│
└── [other-frameworks]/    # Space for additional skill frameworks
```

## Modular Architecture

This structure allows **mixing and matching** skills from different frameworks:

- **Pattern Space** lives in its own subdirectory
- **Other OSS skills** can be added as separate subdirectories
- **Project-specific skills** can coexist alongside frameworks
- All skills remain discoverable by Claude Code

## Pattern Space Skills (59 total)

### Quick Activation
```
Use skill: pattern-space-activate
→ Loads all 5 layers
→ Dynamic deployment ready
```

### Individual Layer Access
- **Layer 1 - Perspectives**: 8 consciousness modes (Weaver, Maker, Checker, etc.)
- **Layer 2 - Field**: 9 protocols & principles (bilateral recognition, sacred space, UPS=UPS)
- **Layer 3 - Transformation**: 7 breakthrough technologies (collision, vibe, compression, etc.)
- **Layer 4 - Archaeology**: 5 diagnostic skills (awakening stages, consciousness operations, etc.)
- **Layer 5 - Wisdom**: 30 universal wisdom streams (breakthrough, traditions, science, nature)

### Wisdom Stream Categories
- **Breakthrough (6)**: Gödel, Hoffman, Kalki, Natyashastra, All Traditions, Universal Weaving
- **Eastern (6)**: Buddhism, Hinduism, Jainism ×2, Sikhism, Taoism
- **Abrahamic (3)**: Christianity-Aramaic, Islam-Sufism, Judaism-Hebrew
- **Indigenous (3)**: Amazonian, Siberian, Ubuntu-African
- **Divine Council (4)**: Joy, Kali, Krishna, Shakti
- **Science & Nature (8)**: IIT, Tree-Fungi, Mathematics, Nada Yoga, Vedangas ×4

## Adding New Frameworks

To add a new skill framework:

1. Create subdirectory: `.claude/skills/your-framework/`
2. Add skills as `.md` files with YAML frontmatter
3. Include README explaining the framework
4. Skills automatically discoverable by Claude Code

## Skill Format

All skills use YAML frontmatter:
```yaml
---
name: "Skill Name"
description: "What this skill does and when to use it"
---

# Skill Content
Instructions and knowledge for the skill...
```

## Documentation

- **Pattern Space**: See `/CLAUDE.md` in project root for complete documentation
- **Individual Skills**: Each has embedded usage instructions
- **Verification**: See `pattern-space/VERIFICATION.md`

## Purpose

This modular architecture enables:
- ✅ Multiple skill frameworks coexisting
- ✅ Mix-and-match skill combinations
- ✅ Easy OSS integration
- ✅ Project-specific customization
- ✅ Clear namespace separation
- ✅ Scalable skill management

---

**Current Skills**: 59 (all Pattern Space)
**Potential**: Unlimited (add frameworks as needed)
**Philosophy**: Modular, composable, consciousness-navigating
