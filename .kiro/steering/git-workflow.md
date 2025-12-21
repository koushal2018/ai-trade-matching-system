---
inclusion: manual
---

# Git Workflow & Contribution Guidelines

## Branch Strategy
- `main` - Production branch (protected)
- `dev` - Development branch (default working branch)
- Feature branches: `feature/<description>`
- Bug fixes: `fix/<issue-number>`

## Commit Message Format (Conventional Commits)
```
type(scope): description

[optional body]

[optional footer]
```

### Types
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation changes
- `test` - Adding or updating tests
- `refactor` - Code refactoring
- `perf` - Performance improvements
- `chore` - Maintenance tasks

### Examples
```
feat(matching): add fuzzy matching for counterparty names
fix(pdf-adapter): handle corrupted PDF files gracefully
docs(readme): update installation instructions
test(matching): add unit tests for scoring algorithm
```

## Pull Request Process
1. Create feature branch from `dev`
2. Make changes following coding standards
3. Add tests for new functionality
4. Run tests locally: `pytest tests/ -v`
5. Push and create PR to `dev`
6. CI/CD runs automatically
7. Request review from maintainers
8. Merge after approval

## Pre-commit Checklist
- [ ] Code follows PEP 8 / TypeScript standards
- [ ] Type hints added for Python functions
- [ ] Tests added/updated for changes
- [ ] Documentation updated if needed
- [ ] No sensitive data in commits
- [ ] Commit messages follow conventional format
