# Git Strategy and Conflict Resolution Guide

> [!abstract] Overview
> This guide provides a comprehensive Git workflow strategy for the French article scraper project, including real-world scenarios, conflict resolution techniques, and best practices. All examples use actual code from this project to demonstrate practical solutions.

## Table of Contents
- [[#Project Git Workflow|Project Git Workflow]]
- [[#Common Git Commands with Examples|Common Git Commands with Examples]]
- [[#Merge Conflict Resolution|Merge Conflict Resolution]]
- [[#Advanced Git Operations|Advanced Git Operations]]
- [[#Emergency Recovery Scenarios|Emergency Recovery Scenarios]]
- [[#Best Practices and Tips|Best Practices and Tips]]

---

## Project Git Workflow

### Branch Strategy

```
main (production-ready)
├── feature/add-lemonde-scraper
├── feature/improve-text-processing
├── bugfix/csv-writer-threading
├── hotfix/parser-crash-fix
└── cleanup/remove-unused-code-and-imports
```

### Naming Conventions
- **Features**: `feature/description-of-feature`
- **Bug fixes**: `bugfix/issue-description`
- **Hotfixes**: `hotfix/critical-issue`
- **Cleanup**: `cleanup/what-being-cleaned`
- **Experiments**: `experiment/new-approach`

---

## Common Git Commands with Examples

### 1. Branch Management

#### Creating and Switching Branches
```bash
# Create new feature branch for adding Le Monde scraper
git checkout -b feature/add-lemonde-scraper

# Switch to existing branch
git checkout main

# Create branch from specific commit
git checkout -b hotfix/parser-crash-fix cd93324

# Delete branch (after merge)
git branch -d feature/add-lemonde-scraper
```

#### Listing and Tracking Branches
```bash
# List all branches
git branch -a

# Show branch with last commit
git branch -v

# Track remote branch
git branch --set-upstream-to=origin/main main
```

### 2. Stashing Changes

**Scenario**: You're working on improving the `FrenchTextProcessor` but need to quickly fix a bug in the CSV writer.

```bash
# You're editing src/utils/french_text_processor.py
# Suddenly need to fix urgent CSV bug

# Stash current changes
git stash push -m "WIP: improving word frequency algorithm"

# Quick fix in CSV writer
git checkout -b hotfix/csv-writer-threading
# ... make fixes ...
git add src/utils/csv_writer.py
git commit -m "Fix threading issue in CSV writer"

# Back to your feature work
git checkout feature/improve-text-processing
git stash pop
```

#### Advanced Stashing
```bash
# Stash only specific files
git stash push src/utils/french_text_processor.py -m "Text processor improvements"

# Stash including untracked files
git stash push -u -m "Include new test files"

# List stashes
git stash list

# Apply specific stash without removing it
git stash apply stash@{1}

# Drop specific stash
git stash drop stash@{0}
```

### 3. Committing Best Practices

#### Atomic Commits
```bash
# Good: Separate logical changes
git add src/scrapers/lemonde_scraper.py
git commit -m "Add Le Monde URL scraper implementation"

git add src/parsers/lemonde_parser.py
git commit -m "Add Le Monde article parser"

git add src/config/website_parser_scrapers_config.py
git commit -m "Register Le Monde scraper in configuration"
```

#### Commit Message Templates
```bash
# Feature commit
git commit -m "Add Le Monde scraper support

- Implement LeMondeScraper class with rate limiting
- Add article parser with metadata extraction
- Configure scraper in website_parser_scrapers_config.py
- Add comprehensive test coverage

Closes #15"

# Bug fix commit
git commit -m "Fix CSV writer threading deadlock

- Replace threading.Lock with class-level lock
- Add timeout handling for file operations
- Prevent concurrent access to same CSV file
- Add error recovery with backup files

Fixes #23"
```

### 4. Merging Strategies

#### Fast-Forward Merge
```bash
# When feature branch is ahead of main with no conflicts
git checkout main
git merge feature/add-lemonde-scraper
```

#### No-Fast-Forward Merge (Preserve History)
```bash
# Preserve feature branch history
git checkout main
git merge --no-ff feature/improve-text-processing
```

#### Squash Merge (Clean History)
```bash
# Combine all feature commits into one
git checkout main
git merge --squash feature/add-lemonde-scraper
git commit -m "Add Le Monde scraper support

Complete implementation including:
- URL scraper with rate limiting
- Article parser with metadata
- Configuration integration
- Test coverage"
```

---

## Merge Conflict Resolution

### Scenario 1: Configuration File Conflict

**Story**: You're adding a new scraper while someone else is modifying the same configuration file.

**Your branch** (`feature/add-lemonde-scraper`):
```python
# src/config/website_parser_scrapers_config.py
SCRAPER_CONFIGS = [
    ScraperConfig(
        name="Slate.fr",
        enabled=True,
        scraper_class="scrapers.slate_fr_scraper.SlateFrURLScraper",
        parser_class="parsers.slate_fr_parser.SlateFrArticleParser",
        scraper_kwargs={"debug": True},
    ),
    # ... other configs ...
    ScraperConfig(
        name="Le Monde",
        enabled=True,
        scraper_class="scrapers.lemonde_scraper.LeMondeScraper",
        parser_class="parsers.lemonde_parser.LeMondeParser",
        scraper_kwargs={"debug": True, "delay": 2.0},
    ),
]
```

**Main branch** (someone else's change):
```python
# src/config/website_parser_scrapers_config.py
SCRAPER_CONFIGS = [
    ScraperConfig(
        name="Slate.fr",
        enabled=True,
        scraper_class="scrapers.slate_fr_scraper.SlateFrURLScraper",
        parser_class="parsers.slate_fr_parser.SlateFrArticleParser",
        scraper_kwargs={"debug": True, "max_retries": 5},  # <-- Modified
    ),
    # ... other configs ...
    ScraperConfig(
        name="Liberation",
        enabled=True,
        scraper_class="scrapers.liberation_scraper.LiberationScraper",
        parser_class="parsers.liberation_parser.LiberationParser",
        scraper_kwargs={"debug": True},
    ),
]
```

**Conflict Resolution Process**:

```bash
# 1. Start the merge
git checkout main
git pull origin main
git checkout feature/add-lemonde-scraper
git merge main

# Git shows conflict:
# Auto-merging src/config/website_parser_scrapers_config.py
# CONFLICT (content): Merge conflict in src/config/website_parser_scrapers_config.py
# Automatic merge failed; fix conflicts and then commit the result.

# 2. Check conflict status
git status
# You have unmerged paths.
#   (fix conflicts and run "git commit")
#   (use "git merge --abort" to abort the merge)
#
# Unmerged paths:
#   (use "git add <file>..." to mark resolution)
#         both modified:   src/config/website_parser_scrapers_config.py
```

**Conflict markers in file**:
```python
# src/config/website_parser_scrapers_config.py
SCRAPER_CONFIGS = [
    ScraperConfig(
        name="Slate.fr",
        enabled=True,
        scraper_class="scrapers.slate_fr_scraper.SlateFrURLScraper",
        parser_class="parsers.slate_fr_parser.SlateFrArticleParser",
<<<<<<< HEAD
        scraper_kwargs={"debug": True},
    ),
    # ... other configs ...
    ScraperConfig(
        name="Le Monde",
        enabled=True,
        scraper_class="scrapers.lemonde_scraper.LeMondeScraper",
        parser_class="parsers.lemonde_parser.LeMondeParser",
        scraper_kwargs={"debug": True, "delay": 2.0},
=======
        scraper_kwargs={"debug": True, "max_retries": 5},
    ),
    # ... other configs ...
    ScraperConfig(
        name="Liberation",
        enabled=True,
        scraper_class="scrapers.liberation_scraper.LiberationScraper",
        parser_class="parsers.liberation_parser.LiberationParser",
        scraper_kwargs={"debug": True},
>>>>>>> main
    ),
]
```

**Resolution**:
```python
# src/config/website_parser_scrapers_config.py
SCRAPER_CONFIGS = [
    ScraperConfig(
        name="Slate.fr",
        enabled=True,
        scraper_class="scrapers.slate_fr_scraper.SlateFrURLScraper",
        parser_class="parsers.slate_fr_parser.SlateFrArticleParser",
        scraper_kwargs={"debug": True, "max_retries": 5},  # Keep their change
    ),
    # ... other configs ...
    ScraperConfig(
        name="Liberation",
        enabled=True,
        scraper_class="scrapers.liberation_scraper.LiberationScraper",
        parser_class="parsers.liberation_parser.LiberationParser",
        scraper_kwargs={"debug": True},
    ),
    ScraperConfig(
        name="Le Monde",  # Add your scraper
        enabled=True,
        scraper_class="scrapers.lemonde_scraper.LeMondeScraper",
        parser_class="parsers.lemonde_parser.LeMondeParser",
        scraper_kwargs={"debug": True, "delay": 2.0},
    ),
]
```

**Complete the merge**:
```bash
# 3. Stage resolved file
git add src/config/website_parser_scrapers_config.py

# 4. Commit the merge
git commit -m "Merge main into feature/add-lemonde-scraper

Resolved conflicts in website_parser_scrapers_config.py:
- Kept max_retries improvement for Slate.fr
- Added Liberation scraper from main
- Added Le Monde scraper from feature branch"

# 5. Verify the merge
git log --oneline --graph -10
```

### Scenario 2: Code Logic Conflict

**Story**: You're refactoring the text processor while someone else is adding new functionality.

**Your branch** (`feature/improve-text-processing`):
```python
# src/utils/french_text_processor.py
def count_word_frequency(self, text: str) -> Dict[str, int]:
    """Improved algorithm with better performance."""
    if not text:
        return {}
    
    # New optimized validation
    if not self._fast_validate(text):
        return {}
    
    # Optimized processing pipeline
    cleaned_text = self._optimized_clean(text)
    words = self._fast_tokenize(cleaned_text)
    
    return dict(Counter(words))
```

**Main branch** (someone else added):
```python
# src/utils/french_text_processor.py
def count_word_frequency(self, text: str) -> Dict[str, int]:
    """Analyze text and return meaningful word frequency counts."""
    validated_text = self.validate_text(text)
    if not validated_text:
        return {}

    cleaned_text = self.clean_text(validated_text)
    words = self.tokenize_french_text(cleaned_text)

    if not words:
        self.logger.debug("No words found after processing")
        return {}

    word_counts = dict(Counter(words))
    
    # NEW: Filter suspicious high-frequency words
    total_words = sum(word_counts.values())
    max_frequency = max(total_words * 0.1, 10)
    
    filtered_words = {
        word: count for word, count in word_counts.items() 
        if count <= max_frequency
    }
    
    return filtered_words
```

**Conflict Resolution**:
```python
# Combined approach - keep both improvements
def count_word_frequency(self, text: str) -> Dict[str, int]:
    """Analyze text with optimized algorithm and frequency filtering."""
    if not text:
        return {}
    
    # Use optimized validation but keep error logging
    validated_text = self._fast_validate(text)
    if not validated_text:
        return {}
    
    # Use optimized processing
    cleaned_text = self._optimized_clean(validated_text)
    words = self._fast_tokenize(cleaned_text)
    
    if not words:
        self.logger.debug("No words found after processing")
        return {}
    
    word_counts = dict(Counter(words))
    
    # Keep the frequency filtering improvement
    total_words = sum(word_counts.values())
    max_frequency = max(total_words * 0.1, 10)
    
    filtered_words = {
        word: count for word, count in word_counts.items() 
        if count <= max_frequency
    }
    
    return filtered_words
```

---

## Advanced Git Operations

### 1. Cherry-Pick

**Scenario**: You need a specific bug fix from another branch without merging everything.

```bash
# You're on main, need CSV fix from feature branch
git log --oneline feature/improve-csv-writer
# a1b2c3d Fix CSV writer threading issue
# e4f5g6h Add CSV validation
# h7i8j9k Improve error handling

# Cherry-pick just the threading fix
git cherry-pick a1b2c3d

# Cherry-pick with custom message
git cherry-pick a1b2c3d --edit
```

**Handling Cherry-Pick Conflicts**:
```bash
# If conflicts occur during cherry-pick
git cherry-pick a1b2c3d
# CONFLICT (content): Merge conflict in src/utils/csv_writer.py

# Fix conflicts in file, then:
git add src/utils/csv_writer.py
git cherry-pick --continue

# Or abort if too complex
git cherry-pick --abort
```

### 2. Rebase

**Scenario**: Clean up your feature branch history before merging.

```bash
# Your feature branch has messy commits
git log --oneline feature/add-lemonde-scraper
# f1a2b3c Add Le Monde scraper (WIP)
# g4h5i6j Fix typo in scraper
# j7k8l9m Add parser
# m1n2o3p Fix parser bug
# p4q5r6s Add tests
# s7t8u9v Fix test failure

# Interactive rebase to clean up
git rebase -i HEAD~6

# Git opens editor with:
# pick f1a2b3c Add Le Monde scraper (WIP)
# pick g4h5i6j Fix typo in scraper
# pick j7k8l9m Add parser
# pick m1n2o3p Fix parser bug
# pick p4q5r6s Add tests
# pick s7t8u9v Fix test failure

# Edit to:
# pick f1a2b3c Add Le Monde scraper (WIP)
# squash g4h5i6j Fix typo in scraper
# pick j7k8l9m Add parser
# squash m1n2o3p Fix parser bug
# pick p4q5r6s Add tests
# squash s7t8u9v Fix test failure
```

**Rebase onto main**:
```bash
# Update feature branch with latest main
git checkout feature/add-lemonde-scraper
git rebase main

# If conflicts occur:
git status
# fix conflicts in files
git add resolved_files
git rebase --continue
```

### 3. Reset Operations

**Scenario**: You made commits but want to undo them.

```bash
# Soft reset - keeps changes staged
git reset --soft HEAD~2

# Mixed reset - keeps changes unstaged (default)
git reset HEAD~2

# Hard reset - discards all changes (DANGEROUS)
git reset --hard HEAD~2

# Reset to specific commit
git reset --hard cd93324
```

**Recovering from Hard Reset**:
```bash
# Find lost commits
git reflog
# cd93324 HEAD@{0}: reset: moving to cd93324
# a1b2c3d HEAD@{1}: commit: Add Le Monde scraper
# e4f5g6h HEAD@{2}: commit: Fix parser

# Recover lost commit
git reset --hard a1b2c3d
```

### 4. Stash Operations Deep Dive

**Complex Stashing Scenarios**:

```bash
# Stash with pathspec
git stash push src/utils/*.py -m "Utils improvements"

# Stash everything except specific files
git stash push --keep-index src/main.py -m "Everything except main"

# Create stash from specific files
git stash push src/parsers/lemonde_parser.py src/scrapers/lemonde_scraper.py -m "Le Monde implementation"

# Apply stash to different branch
git checkout feature/other-feature
git stash apply stash@{1}

# Create branch from stash
git stash branch feature/lemonde-fixes stash@{0}
```

---

## Emergency Recovery Scenarios

### 1. Accidentally Deleted Branch

```bash
# Oh no! Deleted important branch
git branch -d feature/add-lemonde-scraper
# error: The branch 'feature/add-lemonde-scraper' is not fully merged.

# Force deleted it
git branch -D feature/add-lemonde-scraper

# Recovery using reflog
git reflog
# Find the commit where branch was
git checkout -b feature/add-lemonde-scraper a1b2c3d
```

### 2. Wrong Merge Direction

```bash
# Accidentally merged main into feature instead of vice versa
git checkout feature/add-lemonde-scraper
git merge main  # WRONG!

# Undo the merge
git reset --hard HEAD~1

# Correct approach
git checkout main
git merge feature/add-lemonde-scraper
```

### 3. Committed to Wrong Branch

```bash
# Made commit on main instead of feature branch
git checkout main
git commit -m "Add Le Monde scraper"  # OOPS!

# Move commit to correct branch
git branch feature/add-lemonde-scraper  # Creates branch with current commit
git reset --hard HEAD~1  # Remove commit from main
git checkout feature/add-lemonde-scraper  # Switch to correct branch
```

### 4. Pushed Bad Commit

```bash
# Pushed commit with bug to main
git push origin main

# Create fix
git checkout -b hotfix/fix-critical-bug
# ... fix the bug ...
git commit -m "Fix critical bug in parser"

# Fast-track to main
git checkout main
git merge hotfix/fix-critical-bug
git push origin main

# Alternative: Revert the bad commit
git revert a1b2c3d
git push origin main
```

---

## Best Practices and Tips

### 1. Commit Message Standards

```bash
# Format: <type>(<scope>): <description>
#
# <body>
#
# <footer>

# Examples:
feat(scrapers): add Le Monde scraper support
fix(csv): resolve threading deadlock in writer
docs(readme): update installation instructions
refactor(parsers): simplify article extraction logic
test(integration): add offline mode test coverage
```

### 2. Branch Protection Strategy

```bash
# Never work directly on main
git checkout main
git pull origin main
git checkout -b feature/new-feature

# Always test before merging
make test
make format
git add .
git commit -m "..."
```

### 3. Useful Git Aliases

Add to your `~/.gitconfig`:
```bash
[alias]
    st = status
    co = checkout
    br = branch
    ci = commit
    cl = clean -fd
    unstage = reset HEAD --
    last = log -1 HEAD
    visual = !gitk
    tree = log --graph --oneline --all
    amend = commit --amend --no-edit
    uncommit = reset --soft HEAD~1
    recommit = commit --amend --no-edit
```

### 4. Conflict Resolution Tools

```bash
# Configure merge tool
git config merge.tool vimdiff
# or
git config merge.tool code  # VS Code

# Use tool during conflicts
git mergetool

# Check what changed
git diff HEAD~1 HEAD
```

### 5. Working with Remote Branches

```bash
# Track remote branch
git checkout --track origin/feature/new-feature

# Push new branch to remote
git push -u origin feature/add-lemonde-scraper

# Delete remote branch
git push origin --delete feature/old-feature

# Prune deleted remote branches
git remote prune origin
```

---

## Git Workflow Summary

### Daily Workflow
1. **Start day**: `git checkout main && git pull origin main`
2. **Create feature**: `git checkout -b feature/description`
3. **Work & commit**: Regular atomic commits
4. **Before merge**: `git rebase main` (optional)
5. **Merge**: `git checkout main && git merge feature/description`
6. **Clean up**: `git branch -d feature/description`

### Emergency Procedures
1. **Backup first**: `git stash` or `git branch backup-$(date +%s)`
2. **Use reflog**: `git reflog` to find lost commits
3. **Test recovery**: Create test branch to try fixes
4. **Document**: Note what went wrong and how you fixed it

### Collaboration Guidelines
1. **Communicate**: Use descriptive commit messages
2. **Small changes**: Keep PRs focused and reviewable
3. **Test first**: Always run tests before pushing
4. **Rebase vs Merge**: Agree on team strategy
5. **Backup**: Push feature branches regularly

---

## Quick Reference Commands

```bash
# Most common operations
git status                          # Check current state
git add <file>                     # Stage changes
git commit -m "message"            # Commit changes
git push origin <branch>           # Push to remote
git pull origin main               # Get latest changes
git checkout -b <branch>           # Create new branch
git merge <branch>                 # Merge branch
git branch -d <branch>             # Delete branch
git stash                          # Stash changes
git stash pop                      # Apply stashed changes
git log --oneline                  # View commit history
git diff                           # Show changes
git reset --hard HEAD              # Discard all changes
git reflog                         # View reference log
```

---

> [!success] Git Mastery
> This guide provides practical, project-specific examples for every major Git operation you'll encounter. Keep this as reference and practice with your actual code to build confidence with Git workflows.

*Last updated: 2025-07-18*