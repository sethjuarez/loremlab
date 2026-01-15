# Docxer Example: HR Policies Project

This example project demonstrates how to use docxer to generate realistic HR policy
documents for AI/RAG demonstrations.

## Structure

```text
hr-policies/
├── project.yaml          # Project configuration
├── seed/                  # Seed data (markdown files)
│   ├── company-info.md
│   ├── pto-rules.md
│   └── benefits-overview.md
└── output/               # Generated documents (created on generate)
```

## Usage

```bash
cd docxer/examples/hr-policies
docxer generate project.yaml
```

## Goals

The generated documents are designed to answer questions like:

- How much PTO do employees accrue?
- What are the company holidays?
- How do I request time off?
- What benefits are available to employees?
