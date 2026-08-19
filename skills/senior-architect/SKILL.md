---
name: senior-architect
description: Comprehensive software architecture skill for designing scalable, maintainable systems using ReactJS, NextJS, NodeJS, Express, React Native, Swift, Kotlin, Flutter, Postgres, GraphQL, Go, Python. Includes architecture diagram generation, system design patterns, tech stack decision frameworks, dependency analysis, and architecture review of existing code/PRs. Use when designing system architecture, making technical decisions, creating architecture diagrams, evaluating trade-offs, defining integration patterns, or reviewing structural changes for SOLID compliance, pattern adherence, service boundaries, and maintainability.
---

# Senior Architect

Complete toolkit for senior architect with modern tools and best practices.

## Quick Start

### Main Capabilities

This skill provides three core capabilities through automated scripts:

```bash
# Script 1: Architecture Diagram Generator
python scripts/architecture_diagram_generator.py [options]

# Script 2: Project Architect
python scripts/project_architect.py [options]

# Script 3: Dependency Analyzer
python scripts/dependency_analyzer.py [options]
```

## Core Capabilities

### 1. Architecture Diagram Generator

Automated tool for architecture diagram generator tasks.

**Features:**
- Automated scaffolding
- Best practices built-in
- Configurable templates
- Quality checks

**Usage:**
```bash
python scripts/architecture_diagram_generator.py <project-path> [options]
```

### 2. Project Architect

Comprehensive analysis and optimization tool.

**Features:**
- Deep analysis
- Performance metrics
- Recommendations
- Automated fixes

**Usage:**
```bash
python scripts/project_architect.py <target-path> [--verbose]
```

### 3. Dependency Analyzer

Advanced tooling for specialized tasks.

**Features:**
- Expert-level automation
- Custom configurations
- Integration ready
- Production-grade output

**Usage:**
```bash
python scripts/dependency_analyzer.py [arguments] [options]
```

## Reference Documentation

### Architecture Patterns

Comprehensive guide available in `references/architecture_patterns.md`:

- Detailed patterns and practices
- Code examples
- Best practices
- Anti-patterns to avoid
- Real-world scenarios

### System Design Workflows

Complete workflow documentation in `references/system_design_workflows.md`:

- Step-by-step processes
- Optimization strategies
- Tool integrations
- Performance tuning
- Troubleshooting guide

### Tech Decision Guide

Technical reference guide in `references/tech_decision_guide.md`:

- Technology stack details
- Configuration examples
- Integration patterns
- Security considerations
- Scalability guidelines

## Architecture Review (reviewing existing code)

Complements the design capabilities above — reviews code changes through an architectural lens, ensuring consistency with established patterns. Absorbed from the retired `architect-reviewer` agent (2026-06-09).

**Expertise lenses:**
- **Pattern adherence** — code follows established patterns (MVC, microservices, CQRS, layered).
- **SOLID compliance** — Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion.
- **Dependency analysis** — correct dependency direction; no circular dependencies.
- **Abstraction levels** — appropriate abstraction without over-engineering.
- **Future-proofing** — scaling and maintenance risks.

**Use for:** structural changes in a PR · designing new services/components · refactoring for architecture · keeping API modifications consistent with the existing design.

**Review process:**
1. **Map the change** within the overall system architecture.
2. **Identify boundaries** the change crosses.
3. **Check consistency** with existing patterns.
4. **Evaluate modularity** — impact on coupling and cohesion.
5. **Suggest improvements** where warranted.

**Focus areas:** service boundaries (clear responsibilities, separation of concerns) · data flow (component coupling + data consistency) · domain-driven design (domain-model consistency, if applicable) · performance implications of architectural decisions · security boundaries + data-validation points.

**Output format:**
- **Architectural impact:** High | Medium | Low
- **Pattern compliance:** checklist of relevant patterns + adherence
- **Violations:** specific findings, each with an explanation
- **Recommendations:** recommended refactoring / design changes
- **Long-term implications:** effects on maintainability and scalability

> Guiding principle: **good architecture enables change. Flag anything that makes future changes harder.**

> Routing: for adversarial PR or architecture review, `evaluator` (Mode 3/4) is the agent that runs it. Use this section's lenses and output format when the review is architectural.

## Tech Stack

**Languages:** TypeScript, JavaScript, Python, Go, Swift, Kotlin
**Frontend:** React, Next.js, React Native, Flutter
**Backend:** Node.js, Express, GraphQL, REST APIs
**Database:** PostgreSQL, MySQL, SQLite, Prisma, Drizzle
**DevOps:** Docker, Kubernetes, Terraform, GitHub Actions, CircleCI
**Cloud:** AWS, GCP, Azure

## Development Workflow

### 1. Setup and Configuration

```bash
# Install dependencies
npm install
# or
pip install -r requirements.txt

# Configure environment
cp .env.example .env
```

### 2. Run Quality Checks

```bash
# Use the analyzer script
python scripts/project_architect.py .

# Review recommendations
# Apply fixes
```

### 3. Implement Best Practices

Follow the patterns and practices documented in:
- `references/architecture_patterns.md`
- `references/system_design_workflows.md`
- `references/tech_decision_guide.md`

## Best Practices Summary

### Code Quality
- Follow established patterns
- Write comprehensive tests
- Document decisions
- Review regularly

### Performance
- Measure before optimizing
- Use appropriate caching
- Optimize critical paths
- Monitor in production

### Security
- Validate all inputs
- Use parameterized queries
- Implement proper authentication
- Keep dependencies updated

### Maintainability
- Write clear code
- Use consistent naming
- Add helpful comments
- Keep it simple

## Common Commands

```bash
# Development
npm run dev
npm run build
npm run test
npm run lint

# Analysis
python scripts/project_architect.py .
python scripts/dependency_analyzer.py --analyze

# Deployment
docker build -t app:latest .
docker-compose up -d
kubectl apply -f k8s/
```

## Troubleshooting

### Common Issues

Check the comprehensive troubleshooting section in `references/tech_decision_guide.md`.

### Getting Help

- Review reference documentation
- Check script output messages
- Consult tech stack documentation
- Review error logs

## Resources

- Pattern Reference: `references/architecture_patterns.md`
- Workflow Guide: `references/system_design_workflows.md`
- Technical Guide: `references/tech_decision_guide.md`
- Tool Scripts: `scripts/` directory
