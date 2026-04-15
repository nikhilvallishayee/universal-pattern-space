# Contributing to GödelOS

Thank you for your interest in contributing to GödelOS! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation Guidelines](#documentation-guidelines)
- [Pull Request Process](#pull-request-process)
- [Issue Reporting](#issue-reporting)

## Code of Conduct

We are committed to providing a friendly, safe, and welcoming environment for all contributors. Please be respectful and considerate of others when participating in this project.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/yourusername/godelOS.git
   cd godelOS
   ```
3. Set up the development environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e ".[dev]"
   ```
4. Create a new branch for your feature or bugfix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Workflow

1. Make your changes in your feature branch
2. Write tests for your changes
3. Run the tests to ensure they pass:
   ```bash
   pytest
   ```
4. Update documentation if necessary
5. Commit your changes with a descriptive commit message
6. Push your changes to your fork on GitHub
7. Submit a pull request to the main repository

## Coding Standards

- Follow PEP 8 style guidelines for Python code
- Use meaningful variable and function names
- Write docstrings for all functions, classes, and modules
- Keep functions and methods small and focused on a single responsibility
- Use type hints where appropriate
- Format your code using `black` and `isort`:
  ```bash
  black .
  isort .
  ```

## Testing Guidelines

- Write unit tests for all new code
- Ensure all tests pass before submitting a pull request
- Aim for high test coverage of your code
- Test edge cases and error conditions
- Use pytest fixtures and parameterized tests where appropriate

## Documentation Guidelines

- Update the documentation for any changes to the API or behavior
- Document complex algorithms and design decisions
- Use clear and concise language
- Include examples where appropriate
- Keep the README.md up to date

## Pull Request Process

1. Update the README.md and other documentation with details of changes if appropriate
2. Ensure all tests pass and the code meets the coding standards
3. The pull request will be reviewed by at least one maintainer
4. Address any feedback from the review
5. Once approved, your pull request will be merged

## Issue Reporting

- Use the GitHub issue tracker to report bugs or suggest features
- Before creating a new issue, check if a similar issue already exists
- Provide a clear and descriptive title
- Include detailed steps to reproduce the issue
- Include information about your environment (OS, Python version, etc.)
- If possible, include a minimal code example that reproduces the issue

## Module-Specific Contribution Guidelines

### Core Knowledge Representation (KR) System

When contributing to the Core KR System, please ensure:
- Type safety is maintained throughout the system
- Changes to the AST structure are backward compatible or clearly documented as breaking changes
- The unification engine handles all edge cases correctly
- Performance implications of changes are considered

### Inference Engine Architecture

When contributing to the Inference Engine, please ensure:
- New provers implement the BaseProver interface
- Proof objects are properly structured and contain all necessary information
- Resource limits are respected in all inference algorithms
- Changes to the inference coordinator maintain backward compatibility

## Secrets Management & GitHub PAT Setup

### Personal Access Token (PAT) Requirements

Copilot coding agents and automated CI workflows require a GitHub Personal Access Token with specific scopes.

#### Required Scopes

| Scope | Purpose |
|-------|---------|
| `repo` | Full repository access (read/write code, pull requests, issues) |
| `project` | Projects V2 read/write access (required for GitHub Projects board automation) |
| `workflow` | Manage GitHub Actions workflows |
| `read:org` | Read organisation membership (required for org-level Projects) |

> **Important:** The `project` scope is mandatory for Copilot agent tasks that interact with GitHub Projects V2. Without it, project board operations will fail with a 403 error.

#### Creating the PAT

1. Go to **GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens** (recommended) or **Tokens (classic)**.
2. For a **classic PAT**: check `repo`, `project`, `workflow`, and `read:org`.
3. Set an expiry of **90 days maximum** (rotate before expiry — see schedule below).
4. Give it a descriptive name: `godelos-copilot-agent` or similar.

#### Storage Location

- Store the PAT as a **repository secret**: `Settings → Secrets and variables → Actions → New repository secret`.
- Secret name: `COPILOT_PAT` (or `GITHUB_TOKEN` override where applicable).
- **Never** commit the raw token to source code or include it in log output.

#### Rotation Schedule

| Event | Action |
|-------|--------|
| Every 90 days | Revoke old token, generate new one, update repository secret |
| Suspected compromise | Revoke immediately, generate new token, audit recent Actions logs |
| Team member offboarding | Revoke tokens associated with the departing member |

#### Verifying Token Scopes

```bash
curl -s -H "Authorization: token <YOUR_TOKEN>" https://api.github.com/rate_limit \
  -I | grep -i x-oauth-scopes
```

The response header `X-OAuth-Scopes` must include `project` for Projects V2 operations.

#### Environment Variables for Local Development

For local development where Copilot agents or scripts need the PAT, set it in your shell session (never in `.env` files committed to the repo):

```bash
export GITHUB_PAT="ghp_..."
```

Add to your local `.gitignore` any files that might inadvertently capture secrets:
```
.env.local
.secrets
*.token
```

---

## Thank you for contributing to GödelOS!

Your contributions help make this project better for everyone.