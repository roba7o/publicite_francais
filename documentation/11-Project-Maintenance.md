# Project Maintenance - Cleanup and Reset Procedures

> [!abstract] Overview
> This document provides comprehensive procedures for cleaning up, resetting, and maintaining the French article scraper project. It covers environment reset, cache cleanup, log management, dependency updates, and project health monitoring.

## Table of Contents
- [[#Quick Reset Commands|Quick Reset Commands]]
- [[#Environment Cleanup|Environment Cleanup]]
- [[#File System Cleanup|File System Cleanup]]
- [[#Cache and Temporary Files|Cache and Temporary Files]]
- [[#Log Management|Log Management]]
- [[#Dependency Management|Dependency Management]]
- [[#Database and Storage Cleanup|Database and Storage Cleanup]]
- [[#Development Environment Reset|Development Environment Reset]]
- [[#Production Environment Maintenance|Production Environment Maintenance]]
- [[#Automated Maintenance Scripts|Automated Maintenance Scripts]]

---

## Quick Reset Commands

### Emergency Reset (Nuclear Option)

When everything is broken and you need a fresh start:

```bash
#!/bin/bash
# emergency-reset.sh - Complete project reset

set -e

echo "🚨 EMERGENCY RESET - This will delete everything!"
read -p "Are you sure? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Reset cancelled."
    exit 1
fi

echo "1. Stopping any running processes..."
pkill -f "python -m main" || true
pkill -f "french-scraper" || true

echo "2. Removing virtual environment..."
rm -rf venv/
rm -rf .venv/

echo "3. Cleaning output and cache..."
rm -rf src/output/*
rm -rf src/logs/*
rm -rf __pycache__/
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

echo "4. Cleaning test artifacts..."
rm -rf .pytest_cache/
rm -rf htmlcov/
rm -rf .coverage
rm -rf coverage.xml
rm -rf .tox/

echo "5. Cleaning build artifacts..."
rm -rf build/
rm -rf dist/
rm -rf *.egg-info/

echo "6. Recreating virtual environment..."
python -m venv venv
source venv/bin/activate

echo "7. Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "8. Creating required directories..."
mkdir -p src/output
mkdir -p src/logs
chmod 755 src/output src/logs

echo "9. Running smoke test..."
OFFLINE=True DEBUG=True python -m main

echo "✅ Emergency reset completed successfully!"
echo "Environment is ready for use."
```

### Quick Development Reset

For routine cleanup during development:

```bash
#!/bin/bash
# quick-reset.sh - Quick development reset

echo "🔄 Quick development reset..."

# Stop running processes
pkill -f "python -m main" || true

# Clean Python cache
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Clean test artifacts
rm -rf .pytest_cache/
rm -rf htmlcov/
rm -rf .coverage

# Clean output files (keep directory)
rm -f src/output/*.csv
rm -f src/output/*.backup

# Clean logs (keep directory)
rm -f src/logs/*.log
rm -f src/logs/*.json

# Test basic functionality
echo "Testing basic functionality..."
python -c "from config.settings import DEBUG, OFFLINE; print(f'Config OK: DEBUG={DEBUG}, OFFLINE={OFFLINE}')"

echo "✅ Quick reset completed!"
```

---

## Environment Cleanup

### Python Environment Reset

```bash
#!/bin/bash
# reset-python-env.sh - Reset Python environment

echo "🐍 Resetting Python environment..."

# Deactivate current environment
deactivate 2>/dev/null || true

# Remove existing virtual environment
rm -rf venv/
rm -rf .venv/

# Create new virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
if [ -f requirements-dev.txt ]; then
    pip install -r requirements-dev.txt
fi

# Verify installation
echo "Verifying installation..."
python -c "
import sys
print(f'Python version: {sys.version}')
print(f'Virtual env: {sys.prefix}')

# Test key imports
try:
    import requests, bs4, csv
    print('✅ Core dependencies OK')
except ImportError as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)
"

echo "✅ Python environment reset complete!"
```

### Environment Variables Reset

```bash
#!/bin/bash
# reset-env-vars.sh - Reset environment variables

echo "🔧 Resetting environment variables..."

# Unset all project-related environment variables
unset DEBUG
unset OFFLINE
unset OUTPUT_DIR
unset LOG_DIR
unset MAX_ARTICLES_PER_SOURCE
unset PROCESSING_TIMEOUT
unset CONCURRENT_SOURCES
unset MIN_WORD_LENGTH
unset MAX_WORD_LENGTH
unset MIN_WORD_FREQUENCY
unset DISABLED_SOURCES

# Set default values
export DEBUG=False
export OFFLINE=True
export OUTPUT_DIR="src/output"
export LOG_DIR="src/logs"
export MAX_ARTICLES_PER_SOURCE=8
export PROCESSING_TIMEOUT=120

echo "Environment variables reset to defaults:"
echo "  DEBUG=$DEBUG"
echo "  OFFLINE=$OFFLINE"
echo "  OUTPUT_DIR=$OUTPUT_DIR"
echo "  LOG_DIR=$LOG_DIR"
echo "  MAX_ARTICLES_PER_SOURCE=$MAX_ARTICLES_PER_SOURCE"
echo "  PROCESSING_TIMEOUT=$PROCESSING_TIMEOUT"

# Test configuration loading
python -c "
from config.settings import DEBUG, OFFLINE
print(f'Configuration loaded: DEBUG={DEBUG}, OFFLINE={OFFLINE}')
"

echo "✅ Environment variables reset complete!"
```

---

## File System Cleanup

### Output Directory Cleanup

```bash
#!/bin/bash
# clean-output.sh - Clean output directory

echo "📁 Cleaning output directory..."

OUTPUT_DIR="src/output"

if [ ! -d "$OUTPUT_DIR" ]; then
    echo "Creating output directory..."
    mkdir -p "$OUTPUT_DIR"
    chmod 755 "$OUTPUT_DIR"
fi

# Show current contents
echo "Current output files:"
ls -la "$OUTPUT_DIR"

# Calculate total size
total_size=$(du -sh "$OUTPUT_DIR" | cut -f1)
echo "Total output directory size: $total_size"

# Archive old files (older than 7 days)
echo "Archiving old files..."
find "$OUTPUT_DIR" -name "*.csv" -mtime +7 -exec mv {} "$OUTPUT_DIR/archived/" \; 2>/dev/null || true

# Remove backup files
echo "Removing backup files..."
rm -f "$OUTPUT_DIR"/*.backup

# Remove empty files
echo "Removing empty files..."
find "$OUTPUT_DIR" -name "*.csv" -size 0 -delete

# Remove files older than 30 days
echo "Removing files older than 30 days..."
find "$OUTPUT_DIR" -name "*.csv" -mtime +30 -delete

# Show final state
echo "Cleaned output directory:"
ls -la "$OUTPUT_DIR"

new_size=$(du -sh "$OUTPUT_DIR" | cut -f1)
echo "New output directory size: $new_size"

echo "✅ Output directory cleanup complete!"
```

### Test Data Cleanup

```bash
#!/bin/bash
# clean-test-data.sh - Clean test data directory

echo "🧪 Cleaning test data directory..."

TEST_DATA_DIR="src/test_data"

if [ ! -d "$TEST_DATA_DIR" ]; then
    echo "Test data directory not found: $TEST_DATA_DIR"
    exit 1
fi

echo "Current test data structure:"
find "$TEST_DATA_DIR" -type f -name "*.html" | head -10

# Count test files
total_files=$(find "$TEST_DATA_DIR" -name "*.html" | wc -l)
echo "Total test HTML files: $total_files"

# Calculate size
total_size=$(du -sh "$TEST_DATA_DIR" | cut -f1)
echo "Total test data size: $total_size"

# Remove corrupted files (less than 1KB)
echo "Removing corrupted files..."
find "$TEST_DATA_DIR" -name "*.html" -size -1024c -delete

# Remove duplicate files
echo "Removing duplicate files..."
find "$TEST_DATA_DIR" -name "*.html" -exec md5sum {} \; | sort | uniq -D -w 32 | cut -c 35- | xargs rm -f

# Validate remaining files
echo "Validating remaining files..."
for file in $(find "$TEST_DATA_DIR" -name "*.html" | head -5); do
    if [[ $(file "$file") == *"HTML"* ]]; then
        echo "✅ $file"
    else
        echo "❌ $file (not HTML)"
        rm -f "$file"
    fi
done

# Show final state
final_files=$(find "$TEST_DATA_DIR" -name "*.html" | wc -l)
final_size=$(du -sh "$TEST_DATA_DIR" | cut -f1)
echo "Final test data: $final_files files, $final_size"

echo "✅ Test data cleanup complete!"
```

---

## Cache and Temporary Files

### Python Cache Cleanup

```bash
#!/bin/bash
# clean-python-cache.sh - Clean Python cache files

echo "🗑️ Cleaning Python cache files..."

# Count cache files before cleanup
cache_files=$(find . -name "*.pyc" | wc -l)
cache_dirs=$(find . -name "__pycache__" -type d | wc -l)

echo "Found $cache_files .pyc files and $cache_dirs __pycache__ directories"

# Remove .pyc files
echo "Removing .pyc files..."
find . -name "*.pyc" -delete

# Remove __pycache__ directories
echo "Removing __pycache__ directories..."
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Remove .pyo files (Python optimized)
echo "Removing .pyo files..."
find . -name "*.pyo" -delete

# Remove .pyd files (Python extension modules)
echo "Removing .pyd files..."
find . -name "*.pyd" -delete

# Clean pip cache
echo "Cleaning pip cache..."
pip cache purge

# Clean pytest cache
echo "Cleaning pytest cache..."
rm -rf .pytest_cache/

# Clean mypy cache
echo "Cleaning mypy cache..."
rm -rf .mypy_cache/

# Clean coverage cache
echo "Cleaning coverage cache..."
rm -rf htmlcov/
rm -f .coverage
rm -f coverage.xml

# Clean tox cache
echo "Cleaning tox cache..."
rm -rf .tox/

# Clean build artifacts
echo "Cleaning build artifacts..."
rm -rf build/
rm -rf dist/
rm -rf *.egg-info/

# Verify cleanup
remaining_pyc=$(find . -name "*.pyc" | wc -l)
remaining_pycache=$(find . -name "__pycache__" -type d | wc -l)

echo "Cleanup complete: $remaining_pyc .pyc files, $remaining_pycache __pycache__ directories remaining"

echo "✅ Python cache cleanup complete!"
```

### System Cache Cleanup

```bash
#!/bin/bash
# clean-system-cache.sh - Clean system-level cache

echo "🧹 Cleaning system cache..."

# Clean Docker cache (if Docker is available)
if command -v docker &> /dev/null; then
    echo "Cleaning Docker cache..."
    docker system prune -f
    docker volume prune -f
    docker image prune -f
fi

# Clean npm cache (if npm is available)
if command -v npm &> /dev/null; then
    echo "Cleaning npm cache..."
    npm cache clean --force
fi

# Clean system temporary files
echo "Cleaning system temporary files..."
if [ -d "/tmp" ]; then
    find /tmp -name "python*" -type d -user $USER -exec rm -rf {} + 2>/dev/null || true
    find /tmp -name "pip*" -type d -user $USER -exec rm -rf {} + 2>/dev/null || true
fi

# Clean user cache directories
if [ -d "$HOME/.cache" ]; then
    echo "Cleaning user cache directories..."
    rm -rf "$HOME/.cache/pip"
    rm -rf "$HOME/.cache/pytest"
    rm -rf "$HOME/.cache/mypy"
fi

# Clean macOS specific cache (if on macOS)
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Cleaning macOS cache..."
    rm -rf ~/Library/Caches/pip
    rm -rf ~/Library/Caches/pytest
fi

echo "✅ System cache cleanup complete!"
```

---

## Log Management

### Log Rotation and Cleanup

```bash
#!/bin/bash
# manage-logs.sh - Manage application logs

echo "📋 Managing application logs..."

LOG_DIR="src/logs"

if [ ! -d "$LOG_DIR" ]; then
    echo "Creating log directory..."
    mkdir -p "$LOG_DIR"
    chmod 755 "$LOG_DIR"
fi

# Show current log status
echo "Current log directory contents:"
ls -la "$LOG_DIR"

# Calculate total log size
total_size=$(du -sh "$LOG_DIR" 2>/dev/null | cut -f1 || echo "0")
echo "Total log size: $total_size"

# Archive old logs (older than 7 days)
echo "Archiving old logs..."
find "$LOG_DIR" -name "*.log" -mtime +7 -exec gzip {} \; 2>/dev/null || true

# Remove very old logs (older than 30 days)
echo "Removing old compressed logs..."
find "$LOG_DIR" -name "*.log.gz" -mtime +30 -delete

# Remove empty log files
echo "Removing empty log files..."
find "$LOG_DIR" -name "*.log" -size 0 -delete

# Truncate large log files (larger than 100MB)
echo "Truncating large log files..."
find "$LOG_DIR" -name "*.log" -size +100M -exec truncate -s 0 {} \;

# Create log rotation script
cat > "$LOG_DIR/rotate-logs.sh" << 'EOF'
#!/bin/bash
# Log rotation script

LOG_DIR="src/logs"
MAX_SIZE="50M"
MAX_AGE="7"

# Rotate logs larger than MAX_SIZE
for log_file in "$LOG_DIR"/*.log; do
    if [ -f "$log_file" ] && [ $(stat -c%s "$log_file") -gt $(numfmt --from=iec $MAX_SIZE) ]; then
        mv "$log_file" "$log_file.$(date +%Y%m%d_%H%M%S)"
        touch "$log_file"
        echo "Rotated: $log_file"
    fi
done

# Compress old rotated logs
find "$LOG_DIR" -name "*.log.*" -mtime +1 -exec gzip {} \;

# Remove old compressed logs
find "$LOG_DIR" -name "*.log.*.gz" -mtime +$MAX_AGE -delete

echo "Log rotation complete"
EOF

chmod +x "$LOG_DIR/rotate-logs.sh"

# Show final log status
echo "Log directory after cleanup:"
ls -la "$LOG_DIR"

new_size=$(du -sh "$LOG_DIR" 2>/dev/null | cut -f1 || echo "0")
echo "New log size: $new_size"

echo "✅ Log management complete!"
```

### Log Analysis and Monitoring

```bash
#!/bin/bash
# analyze-logs.sh - Analyze application logs

echo "📊 Analyzing application logs..."

LOG_DIR="src/logs"

if [ ! -d "$LOG_DIR" ]; then
    echo "Log directory not found: $LOG_DIR"
    exit 1
fi

# Find log files
log_files=$(find "$LOG_DIR" -name "*.log" | head -10)

if [ -z "$log_files" ]; then
    echo "No log files found in $LOG_DIR"
    exit 1
fi

echo "Analyzing log files:"
echo "$log_files"

# Analyze error patterns
echo "=== Error Analysis ==="
grep -i "error\|exception\|failed\|timeout" $log_files | head -20

# Analyze performance patterns
echo "=== Performance Analysis ==="
grep -i "processing.*completed\|took.*seconds" $log_files | tail -10

# Analyze source activity
echo "=== Source Activity ==="
grep -i "source.*processing\|extracted.*urls" $log_files | tail -10

# Count log levels
echo "=== Log Level Summary ==="
for level in ERROR WARNING INFO DEBUG; do
    count=$(grep -c "\[$level\]" $log_files 2>/dev/null || echo "0")
    echo "$level: $count"
done

# Check for concerning patterns
echo "=== Health Check ==="
error_count=$(grep -c "ERROR\|Exception" $log_files 2>/dev/null || echo "0")
if [ "$error_count" -gt 10 ]; then
    echo "⚠️ High error count: $error_count"
else
    echo "✅ Error count acceptable: $error_count"
fi

timeout_count=$(grep -c "timeout\|Timeout" $log_files 2>/dev/null || echo "0")
if [ "$timeout_count" -gt 5 ]; then
    echo "⚠️ High timeout count: $timeout_count"
else
    echo "✅ Timeout count acceptable: $timeout_count"
fi

echo "✅ Log analysis complete!"
```

---

## Dependency Management

### Dependency Update and Cleanup

```bash
#!/bin/bash
# update-dependencies.sh - Update and clean dependencies

echo "📦 Managing dependencies..."

# Backup current requirements
echo "Backing up current requirements..."
cp requirements.txt requirements.txt.backup
if [ -f requirements-dev.txt ]; then
    cp requirements-dev.txt requirements-dev.txt.backup
fi

# Check for outdated packages
echo "Checking for outdated packages..."
pip list --outdated

# Update pip itself
echo "Updating pip..."
pip install --upgrade pip

# Update all packages
echo "Updating all packages..."
pip install --upgrade -r requirements.txt

# Update development dependencies
if [ -f requirements-dev.txt ]; then
    echo "Updating development dependencies..."
    pip install --upgrade -r requirements-dev.txt
fi

# Check for security vulnerabilities
echo "Checking for security vulnerabilities..."
pip install safety
safety check

# Generate new requirements file
echo "Generating new requirements file..."
pip freeze > requirements-new.txt

# Test with new requirements
echo "Testing with new requirements..."
python -c "
import sys
try:
    import requests, bs4, csv
    from config.settings import DEBUG, OFFLINE
    print('✅ All imports successful')
except ImportError as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)
"

# Run quick test
echo "Running quick test..."
OFFLINE=True DEBUG=True timeout 30 python -m main

echo "New requirements generated: requirements-new.txt"
echo "To apply: mv requirements-new.txt requirements.txt"
echo "To restore: mv requirements.txt.backup requirements.txt"

echo "✅ Dependency management complete!"
```

### Dependency Audit

```bash
#!/bin/bash
# audit-dependencies.sh - Audit project dependencies

echo "🔍 Auditing dependencies..."

# Check for unused packages
echo "=== Unused Packages ==="
pip install pipreqs
pipreqs --force .
echo "Generated requirements from actual imports: requirements.txt"

# Compare with current requirements
echo "=== Dependency Comparison ==="
if [ -f requirements.txt.backup ]; then
    echo "Packages only in current requirements:"
    comm -23 <(sort requirements.txt.backup) <(sort requirements.txt)
    
    echo "Packages only in generated requirements:"
    comm -13 <(sort requirements.txt.backup) <(sort requirements.txt)
fi

# Check for conflicting dependencies
echo "=== Dependency Conflicts ==="
pip check

# Check for vulnerable packages
echo "=== Security Vulnerabilities ==="
pip install pip-audit
pip-audit

# Check license compatibility
echo "=== License Information ==="
pip install pip-licenses
pip-licenses --format=table

# Generate dependency tree
echo "=== Dependency Tree ==="
pip install pipdeptree
pipdeptree

echo "✅ Dependency audit complete!"
```

---

## Database and Storage Cleanup

### CSV Output Cleanup

```bash
#!/bin/bash
# clean-csv-output.sh - Clean CSV output files

echo "📊 Cleaning CSV output files..."

OUTPUT_DIR="src/output"

if [ ! -d "$OUTPUT_DIR" ]; then
    echo "Output directory not found: $OUTPUT_DIR"
    exit 1
fi

# Show current CSV files
echo "Current CSV files:"
ls -la "$OUTPUT_DIR"/*.csv 2>/dev/null || echo "No CSV files found"

# Count total records
total_records=0
for file in "$OUTPUT_DIR"/*.csv; do
    if [ -f "$file" ]; then
        records=$(wc -l < "$file")
        total_records=$((total_records + records))
        echo "$(basename "$file"): $records records"
    fi
done
echo "Total records: $total_records"

# Identify duplicate entries
echo "=== Checking for duplicates ==="
duplicate_count=0
for file in "$OUTPUT_DIR"/*.csv; do
    if [ -f "$file" ]; then
        duplicates=$(sort "$file" | uniq -d | wc -l)
        if [ "$duplicates" -gt 0 ]; then
            echo "$(basename "$file"): $duplicates duplicate entries"
            duplicate_count=$((duplicate_count + duplicates))
        fi
    fi
done
echo "Total duplicates: $duplicate_count"

# Clean duplicate entries
echo "=== Removing duplicates ==="
for file in "$OUTPUT_DIR"/*.csv; do
    if [ -f "$file" ]; then
        # Create backup
        cp "$file" "$file.backup"
        
        # Remove duplicates while preserving header
        head -1 "$file" > "$file.tmp"
        tail -n +2 "$file" | sort -u >> "$file.tmp"
        mv "$file.tmp" "$file"
        
        echo "Cleaned: $(basename "$file")"
    fi
done

# Validate CSV structure
echo "=== Validating CSV structure ==="
for file in "$OUTPUT_DIR"/*.csv; do
    if [ -f "$file" ]; then
        # Check if file has expected columns
        header=$(head -1 "$file")
        if [[ "$header" == *"word"* && "$header" == *"context"* && "$header" == *"source"* ]]; then
            echo "✅ $(basename "$file"): Valid structure"
        else
            echo "❌ $(basename "$file"): Invalid structure"
        fi
    fi
done

# Remove empty files
echo "=== Removing empty files ==="
find "$OUTPUT_DIR" -name "*.csv" -size 0 -delete

# Remove backup files older than 1 day
echo "=== Cleaning old backups ==="
find "$OUTPUT_DIR" -name "*.backup" -mtime +1 -delete

# Show final statistics
echo "=== Final Statistics ==="
file_count=$(ls -1 "$OUTPUT_DIR"/*.csv 2>/dev/null | wc -l)
total_size=$(du -sh "$OUTPUT_DIR" 2>/dev/null | cut -f1 || echo "0")
echo "CSV files: $file_count"
echo "Total size: $total_size"

echo "✅ CSV output cleanup complete!"
```

### Storage Optimization

```bash
#!/bin/bash
# optimize-storage.sh - Optimize storage usage

echo "💾 Optimizing storage usage..."

# Check disk usage
echo "=== Disk Usage Analysis ==="
df -h

# Check project directory size
echo "=== Project Directory Size ==="
du -sh .
du -sh */ | sort -hr

# Find large files
echo "=== Large Files (>10MB) ==="
find . -type f -size +10M -exec ls -lh {} \; | sort -k5 -hr

# Find files that can be compressed
echo "=== Compressible Files ==="
find . -name "*.log" -size +1M -exec ls -lh {} \;
find . -name "*.html" -size +1M -exec ls -lh {} \;
find . -name "*.csv" -size +10M -exec ls -lh {} \;

# Compress large log files
echo "=== Compressing large files ==="
find . -name "*.log" -size +1M -exec gzip {} \;
find . -name "*.html" -size +1M -exec gzip {} \;

# Archive old CSV files
echo "=== Archiving old CSV files ==="
if [ ! -d "archive" ]; then
    mkdir archive
fi

find src/output -name "*.csv" -mtime +30 -exec mv {} archive/ \;

# Clean up git objects
echo "=== Cleaning git objects ==="
git gc --prune=now

# Show final disk usage
echo "=== Final Disk Usage ==="
du -sh .

echo "✅ Storage optimization complete!"
```

---

## Development Environment Reset

### Complete Development Reset

```bash
#!/bin/bash
# reset-dev-environment.sh - Complete development environment reset

echo "🔄 Resetting development environment..."

# 1. Clean Python environment
echo "1. Cleaning Python environment..."
deactivate 2>/dev/null || true
rm -rf venv/
rm -rf .venv/

# 2. Clean cache and temporary files
echo "2. Cleaning cache and temporary files..."
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
rm -rf .pytest_cache/
rm -rf htmlcov/
rm -rf .coverage
rm -rf .mypy_cache/
rm -rf .tox/
rm -rf build/
rm -rf dist/
rm -rf *.egg-info/

# 3. Clean output and logs
echo "3. Cleaning output and logs..."
rm -f src/output/*.csv
rm -f src/output/*.backup
rm -f src/logs/*.log
rm -f src/logs/*.json

# 4. Reset git state (optional)
echo "4. Checking git state..."
if [ -d ".git" ]; then
    git status
    echo "Git state preserved. Run 'git clean -fd' to remove untracked files."
fi

# 5. Recreate virtual environment
echo "5. Creating new virtual environment..."
python -m venv venv
source venv/bin/activate

# 6. Install dependencies
echo "6. Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

if [ -f requirements-dev.txt ]; then
    pip install -r requirements-dev.txt
fi

# 7. Setup pre-commit hooks
echo "7. Setting up pre-commit hooks..."
if command -v pre-commit &> /dev/null; then
    pre-commit install
fi

# 8. Create required directories
echo "8. Creating required directories..."
mkdir -p src/output
mkdir -p src/logs
chmod 755 src/output src/logs

# 9. Run validation tests
echo "9. Running validation tests..."
python -c "
import sys
try:
    from config.settings import DEBUG, OFFLINE
    from utils.csv_writer import DailyCSVWriter
    from utils.french_text_processor import FrenchTextProcessor
    print('✅ All imports successful')
except ImportError as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)
"

# 10. Run smoke test
echo "10. Running smoke test..."
OFFLINE=True DEBUG=True timeout 60 python -m main

echo "✅ Development environment reset complete!"
echo "Environment ready for development."
```

### IDE and Editor Configuration Reset

```bash
#!/bin/bash
# reset-ide-config.sh - Reset IDE configuration

echo "🔧 Resetting IDE configuration..."

# VSCode settings
if [ -d ".vscode" ]; then
    echo "Resetting VSCode settings..."
    
    # Backup current settings
    cp .vscode/settings.json .vscode/settings.json.backup 2>/dev/null || true
    
    # Create clean settings
    cat > .vscode/settings.json << 'EOF'
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": false,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "python.testing.pytestEnabled": true,
    "python.testing.unittestEnabled": false,
    "python.testing.pytestArgs": [
        "tests"
    ],
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true,
        ".pytest_cache": true,
        "htmlcov": true,
        ".coverage": true,
        ".mypy_cache": true
    }
}
EOF

    # Update launch configuration
    cat > .vscode/launch.json << 'EOF'
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Main Module",
            "type": "python",
            "request": "launch",
            "module": "main",
            "env": {
                "OFFLINE": "True",
                "DEBUG": "True"
            },
            "console": "integratedTerminal"
        },
        {
            "name": "Python: Current File",
            "type": "python",
            "request": "launch",
            "program": "${file}",
            "console": "integratedTerminal"
        }
    ]
}
EOF

    echo "✅ VSCode configuration reset"
fi

# PyCharm settings
if [ -d ".idea" ]; then
    echo "Resetting PyCharm settings..."
    
    # Reset run configurations
    rm -rf .idea/runConfigurations/
    mkdir -p .idea/runConfigurations/
    
    # Create main run configuration
    cat > .idea/runConfigurations/main.xml << 'EOF'
<component name="ProjectRunConfigurationManager">
  <configuration default="false" name="main" type="PythonConfigurationType" factoryName="Python">
    <module name="french-scraper" />
    <option name="INTERPRETER_OPTIONS" value="" />
    <option name="PARENT_ENVS" value="true" />
    <envs>
      <env name="OFFLINE" value="True" />
      <env name="DEBUG" value="True" />
    </envs>
    <option name="SDK_HOME" value="" />
    <option name="WORKING_DIRECTORY" value="$PROJECT_DIR$" />
    <option name="IS_MODULE_SDK" value="true" />
    <option name="ADD_CONTENT_ROOTS" value="true" />
    <option name="ADD_SOURCE_ROOTS" value="true" />
    <option name="SCRIPT_NAME" value="$PROJECT_DIR$/main.py" />
    <option name="PARAMETERS" value="" />
    <option name="SHOW_COMMAND_LINE" value="false" />
    <option name="EMULATE_TERMINAL" value="false" />
    <option name="MODULE_MODE" value="false" />
    <option name="REDIRECT_INPUT" value="false" />
    <option name="INPUT_FILE" value="" />
    <method v="2" />
  </configuration>
</component>
EOF

    echo "✅ PyCharm configuration reset"
fi

# Vim/Neovim settings
if [ -f ".vimrc" ] || [ -f "init.vim" ]; then
    echo "Vim configuration found, leaving unchanged"
fi

echo "✅ IDE configuration reset complete!"
```

---

## Production Environment Maintenance

### Production Health Check

```bash
#!/bin/bash
# production-health-check.sh - Check production environment health

echo "🏥 Production health check..."

# Check service status
echo "=== Service Status ==="
if command -v systemctl &> /dev/null; then
    systemctl status french-scraper || echo "Service not found"
fi

# Check running processes
echo "=== Running Processes ==="
ps aux | grep -i french | grep -v grep

# Check disk usage
echo "=== Disk Usage ==="
df -h

# Check memory usage
echo "=== Memory Usage ==="
free -h

# Check CPU usage
echo "=== CPU Usage ==="
top -bn1 | grep "Cpu(s)"

# Check network connectivity
echo "=== Network Connectivity ==="
ping -c 3 google.com || echo "Internet connectivity issues"

# Check target websites
echo "=== Target Website Status ==="
for url in "https://www.slate.fr" "https://www.franceinfo.fr" "https://www.tf1info.fr" "https://www.ladepeche.fr"; do
    if curl -s --head "$url" | grep "200 OK" > /dev/null; then
        echo "✅ $url"
    else
        echo "❌ $url"
    fi
done

# Check recent outputs
echo "=== Recent Outputs ==="
if [ -d "src/output" ]; then
    recent_files=$(find src/output -name "*.csv" -mtime -1 | wc -l)
    echo "Recent CSV files (last 24h): $recent_files"
    
    if [ "$recent_files" -gt 0 ]; then
        echo "✅ Recent output files found"
    else
        echo "⚠️ No recent output files"
    fi
fi

# Check error logs
echo "=== Error Log Summary ==="
if [ -d "src/logs" ]; then
    error_count=$(grep -c "ERROR" src/logs/*.log 2>/dev/null || echo "0")
    echo "Recent errors: $error_count"
    
    if [ "$error_count" -gt 10 ]; then
        echo "⚠️ High error count"
        echo "Recent errors:"
        grep "ERROR" src/logs/*.log 2>/dev/null | tail -5
    else
        echo "✅ Error count acceptable"
    fi
fi

echo "✅ Production health check complete!"
```

### Production Maintenance

```bash
#!/bin/bash
# production-maintenance.sh - Production maintenance tasks

echo "🔧 Production maintenance..."

# Create maintenance flag
touch /tmp/maintenance.flag

# Log maintenance start
echo "$(date): Starting maintenance" >> src/logs/maintenance.log

# 1. Backup current data
echo "1. Backing up current data..."
backup_dir="backup/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$backup_dir"
cp -r src/output/* "$backup_dir/"
cp -r src/logs/* "$backup_dir/"

# 2. Rotate logs
echo "2. Rotating logs..."
src/logs/rotate-logs.sh

# 3. Clean old outputs
echo "3. Cleaning old outputs..."
find src/output -name "*.csv" -mtime +30 -exec mv {} archive/ \;

# 4. Update dependencies (if safe)
echo "4. Checking dependencies..."
pip list --outdated | head -10

# 5. Run health checks
echo "5. Running health checks..."
OFFLINE=True DEBUG=True timeout 60 python -m main

# 6. Monitor system resources
echo "6. System resource check..."
df -h
free -h

# 7. Clean temporary files
echo "7. Cleaning temporary files..."
find /tmp -name "*python*" -user $USER -mtime +1 -exec rm -rf {} + 2>/dev/null || true

# 8. Validate configuration
echo "8. Validating configuration..."
python -c "
from config.settings import DEBUG, OFFLINE
from config.website_parser_scrapers_config import SCRAPER_CONFIGS
enabled_sources = [c for c in SCRAPER_CONFIGS if c.enabled]
print(f'Configuration valid: {len(enabled_sources)} enabled sources')
"

# Remove maintenance flag
rm -f /tmp/maintenance.flag

# Log maintenance end
echo "$(date): Maintenance completed" >> src/logs/maintenance.log

echo "✅ Production maintenance complete!"
```

---

## Automated Maintenance Scripts

### Cron Job Setup

```bash
#!/bin/bash
# setup-cron-jobs.sh - Setup automated maintenance cron jobs

echo "⏰ Setting up cron jobs..."

# Create cron job directory
mkdir -p scripts/cron

# Create daily maintenance script
cat > scripts/cron/daily-maintenance.sh << 'EOF'
#!/bin/bash
# Daily maintenance tasks

cd /path/to/french-scraper

# Rotate logs
src/logs/rotate-logs.sh

# Clean cache
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Clean old outputs
find src/output -name "*.csv" -mtime +7 -exec gzip {} \;
find src/output -name "*.csv.gz" -mtime +30 -delete

# Health check
OFFLINE=True DEBUG=True timeout 60 python -m main

# Log maintenance
echo "$(date): Daily maintenance completed" >> src/logs/maintenance.log
EOF

# Create weekly maintenance script
cat > scripts/cron/weekly-maintenance.sh << 'EOF'
#!/bin/bash
# Weekly maintenance tasks

cd /path/to/french-scraper

# Full cleanup
scripts/clean-python-cache.sh
scripts/clean-output.sh
scripts/manage-logs.sh

# Backup important data
backup_dir="backup/$(date +%Y%m%d)"
mkdir -p "$backup_dir"
cp -r src/output/*.csv "$backup_dir/" 2>/dev/null || true
cp -r src/logs/*.log "$backup_dir/" 2>/dev/null || true

# Update dependencies check
pip list --outdated > reports/outdated-packages.txt

# Health report
scripts/production-health-check.sh > reports/health-report.txt

# Log maintenance
echo "$(date): Weekly maintenance completed" >> src/logs/maintenance.log
EOF

# Make scripts executable
chmod +x scripts/cron/*.sh

# Create crontab entries
cat > scripts/cron/crontab.txt << 'EOF'
# French Scraper Maintenance Cron Jobs

# Daily maintenance at 2 AM
0 2 * * * /path/to/french-scraper/scripts/cron/daily-maintenance.sh

# Weekly maintenance on Sunday at 3 AM
0 3 * * 0 /path/to/french-scraper/scripts/cron/weekly-maintenance.sh

# Hourly log rotation check
0 * * * * /path/to/french-scraper/src/logs/rotate-logs.sh

# Daily health check at 6 AM
0 6 * * * /path/to/french-scraper/scripts/production-health-check.sh
EOF

echo "Cron jobs configuration created in scripts/cron/crontab.txt"
echo "To install: crontab scripts/cron/crontab.txt"
echo "To view: crontab -l"
echo "To remove: crontab -r"

echo "✅ Cron jobs setup complete!"
```

### Automated Monitoring

```bash
#!/bin/bash
# setup-monitoring.sh - Setup automated monitoring

echo "📊 Setting up automated monitoring..."

# Create monitoring directory
mkdir -p scripts/monitoring

# Create system monitor
cat > scripts/monitoring/system-monitor.sh << 'EOF'
#!/bin/bash
# System monitoring script

REPORT_FILE="reports/system-report-$(date +%Y%m%d).txt"
mkdir -p reports

{
    echo "System Report - $(date)"
    echo "=============================="
    echo
    
    echo "Disk Usage:"
    df -h
    echo
    
    echo "Memory Usage:"
    free -h
    echo
    
    echo "CPU Usage:"
    top -bn1 | grep "Cpu(s)"
    echo
    
    echo "Running Processes:"
    ps aux | grep -i french | grep -v grep
    echo
    
    echo "Network Status:"
    netstat -tuln | grep LISTEN
    echo
    
    echo "Recent Errors:"
    if [ -d "src/logs" ]; then
        grep -i "error\|exception" src/logs/*.log 2>/dev/null | tail -10
    fi
    
} > "$REPORT_FILE"

echo "System report generated: $REPORT_FILE"
EOF

# Create application monitor
cat > scripts/monitoring/app-monitor.sh << 'EOF'
#!/bin/bash
# Application monitoring script

REPORT_FILE="reports/app-report-$(date +%Y%m%d).txt"
mkdir -p reports

{
    echo "Application Report - $(date)"
    echo "=============================="
    echo
    
    echo "Recent Outputs:"
    if [ -d "src/output" ]; then
        ls -la src/output/*.csv 2>/dev/null | tail -10
    fi
    echo
    
    echo "Log Summary:"
    if [ -d "src/logs" ]; then
        for level in ERROR WARNING INFO; do
            count=$(grep -c "\[$level\]" src/logs/*.log 2>/dev/null || echo "0")
            echo "$level: $count"
        done
    fi
    echo
    
    echo "Configuration Status:"
    python -c "
from config.settings import DEBUG, OFFLINE
from config.website_parser_scrapers_config import SCRAPER_CONFIGS
enabled = [c for c in SCRAPER_CONFIGS if c.enabled]
print(f'Mode: DEBUG={DEBUG}, OFFLINE={OFFLINE}')
print(f'Enabled sources: {len(enabled)}')
for c in enabled:
    print(f'  - {c.name}')
"
    echo
    
    echo "Health Check:"
    if OFFLINE=True DEBUG=True timeout 30 python -m main > /dev/null 2>&1; then
        echo "✅ Health check passed"
    else
        echo "❌ Health check failed"
    fi
    
} > "$REPORT_FILE"

echo "Application report generated: $REPORT_FILE"
EOF

# Create alert system
cat > scripts/monitoring/alert-system.sh << 'EOF'
#!/bin/bash
# Alert system for critical issues

ALERT_EMAIL="admin@example.com"
ALERT_SLACK_WEBHOOK="https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"

check_disk_space() {
    disk_usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ "$disk_usage" -gt 90 ]; then
        echo "CRITICAL: Disk usage is ${disk_usage}%"
        return 1
    fi
    return 0
}

check_memory_usage() {
    mem_usage=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
    if [ "$mem_usage" -gt 90 ]; then
        echo "CRITICAL: Memory usage is ${mem_usage}%"
        return 1
    fi
    return 0
}

check_error_rate() {
    if [ -d "src/logs" ]; then
        error_count=$(grep -c "ERROR" src/logs/*.log 2>/dev/null || echo "0")
        if [ "$error_count" -gt 20 ]; then
            echo "CRITICAL: High error rate: $error_count errors"
            return 1
        fi
    fi
    return 0
}

check_recent_output() {
    if [ -d "src/output" ]; then
        recent_files=$(find src/output -name "*.csv" -mtime -1 | wc -l)
        if [ "$recent_files" -eq 0 ]; then
            echo "WARNING: No recent output files"
            return 1
        fi
    fi
    return 0
}

# Run all checks
alerts=""
check_disk_space || alerts="$alerts$(check_disk_space)\n"
check_memory_usage || alerts="$alerts$(check_memory_usage)\n"
check_error_rate || alerts="$alerts$(check_error_rate)\n"
check_recent_output || alerts="$alerts$(check_recent_output)\n"

# Send alerts if any issues found
if [ -n "$alerts" ]; then
    echo -e "French Scraper Alerts:\n$alerts"
    
    # Send email (requires mailutils)
    if command -v mail &> /dev/null; then
        echo -e "$alerts" | mail -s "French Scraper Alerts" "$ALERT_EMAIL"
    fi
    
    # Send Slack notification (requires curl)
    if command -v curl &> /dev/null && [ -n "$ALERT_SLACK_WEBHOOK" ]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"French Scraper Alerts:\n$alerts\"}" \
            "$ALERT_SLACK_WEBHOOK"
    fi
fi
EOF

# Make scripts executable
chmod +x scripts/monitoring/*.sh

# Create monitoring cron jobs
cat > scripts/monitoring/monitoring-cron.txt << 'EOF'
# Monitoring Cron Jobs

# System monitoring every 4 hours
0 */4 * * * /path/to/french-scraper/scripts/monitoring/system-monitor.sh

# Application monitoring every 2 hours
0 */2 * * * /path/to/french-scraper/scripts/monitoring/app-monitor.sh

# Alert system check every 30 minutes
*/30 * * * * /path/to/french-scraper/scripts/monitoring/alert-system.sh
EOF

echo "Monitoring scripts created in scripts/monitoring/"
echo "To enable monitoring: crontab scripts/monitoring/monitoring-cron.txt"

echo "✅ Monitoring setup complete!"
```

---

## Maintenance Schedules

### Daily Maintenance Checklist

- [ ] **Log Rotation**: Rotate logs larger than 50MB
- [ ] **Cache Cleanup**: Remove Python cache files
- [ ] **Output Validation**: Check recent CSV outputs
- [ ] **Health Check**: Run offline mode test
- [ ] **Disk Usage**: Monitor disk space usage
- [ ] **Error Review**: Check error logs for patterns

### Weekly Maintenance Checklist

- [ ] **Full Cleanup**: Run complete cleanup scripts
- [ ] **Dependency Check**: Check for outdated packages
- [ ] **Performance Review**: Analyze performance metrics
- [ ] **Backup Validation**: Verify backup integrity
- [ ] **Documentation Update**: Update documentation if needed
- [ ] **Security Scan**: Run security vulnerability scan

### Monthly Maintenance Checklist

- [ ] **Dependency Updates**: Update all dependencies
- [ ] **Configuration Review**: Review and optimize configuration
- [ ] **Performance Optimization**: Optimize system performance
- [ ] **Storage Cleanup**: Archive old data
- [ ] **Security Updates**: Apply security patches
- [ ] **Documentation Review**: Review and update documentation

### Quarterly Maintenance Checklist

- [ ] **Full System Review**: Complete system audit
- [ ] **Architecture Review**: Assess architecture improvements
- [ ] **Performance Benchmarking**: Benchmark system performance
- [ ] **Disaster Recovery Test**: Test backup and recovery procedures
- [ ] **Team Training**: Update team on new procedures
- [ ] **Tool Updates**: Update development and monitoring tools

---

## Emergency Procedures

### Production Outage Response

```bash
#!/bin/bash
# emergency-response.sh - Emergency response procedures

echo "🚨 Emergency response activated!"

# 1. Immediate assessment
echo "1. Assessing situation..."
systemctl status french-scraper || echo "Service not running"
ps aux | grep -i french | grep -v grep
df -h
free -h

# 2. Quick fixes
echo "2. Attempting quick fixes..."
# Restart service
systemctl restart french-scraper || echo "Service restart failed"

# Clear cache
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# 3. Rollback if needed
echo "3. Checking if rollback needed..."
if [ -d "backup" ]; then
    latest_backup=$(ls -t backup/ | head -1)
    echo "Latest backup available: $latest_backup"
fi

# 4. Notify team
echo "4. Notifying team..."
echo "Emergency response completed at $(date)" >> src/logs/emergency.log

echo "✅ Emergency response completed!"
```

### Data Recovery Procedures

```bash
#!/bin/bash
# data-recovery.sh - Data recovery procedures

echo "💾 Data recovery procedures..."

# 1. Assess data loss
echo "1. Assessing data loss..."
if [ -d "src/output" ]; then
    echo "Output directory exists"
    ls -la src/output/
else
    echo "Output directory missing!"
    mkdir -p src/output
fi

# 2. Restore from backup
echo "2. Restoring from backup..."
if [ -d "backup" ]; then
    latest_backup=$(ls -t backup/ | head -1)
    if [ -n "$latest_backup" ]; then
        echo "Restoring from: $latest_backup"
        cp -r "backup/$latest_backup"/* src/output/
    fi
else
    echo "No backup directory found!"
fi

# 3. Regenerate missing data
echo "3. Regenerating missing data..."
OFFLINE=True DEBUG=True timeout 300 python -m main

# 4. Validate recovery
echo "4. Validating recovery..."
recent_files=$(find src/output -name "*.csv" -mtime -1 | wc -l)
if [ "$recent_files" -gt 0 ]; then
    echo "✅ Recovery successful"
else
    echo "❌ Recovery failed"
fi

echo "✅ Data recovery procedures completed!"
```

---

## Cross-References

- [[08-Adding-News-Source]] - Adding new sources to maintenance
- [[09-Troubleshooting]] - Troubleshooting maintenance issues
- [[10-CI-CD]] - CI/CD pipeline maintenance
- [[04-Testing]] - Testing maintenance procedures
- [[05-Utils]] - Utility functions for maintenance
- [[06-Config]] - Configuration management during maintenance