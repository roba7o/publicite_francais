# Migration Rollback System

This guide explains how to use the migration rollback functionality.

## How It Works

### Migration Naming Convention
- **Forward migration**: `003_example_add_article_tags.sql`
- **Rollback migration**: `003_rollback_example_add_article_tags.sql`

The rollback file must:
1. Start with the same number as the forward migration
2. Include `_rollback_` in the filename
3. Contain SQL to undo the forward migration

### Commands

```bash
# Apply migrations
make db-migrate

# Check what would be applied (dry run)
make db-migrate-dry

# Rollback to specific migration
make db-rollback TARGET=002

# Check what would be rolled back (dry run)
PYTHONPATH=src python database/migrations/run_migrations.py --rollback 002 --dry-run
```

## Example Workflow

### 1. Create Forward Migration
```bash
# database/migrations/003_example_add_article_tags.sql
-- Add new functionality
CREATE TABLE article_tags (...);
```

### 2. Create Rollback Migration
```bash
# database/migrations/003_rollback_example_add_article_tags.sql  
-- Remove the functionality
DROP TABLE article_tags CASCADE;
```

### 3. Apply Migration
```bash
make db-migrate
# ✓ Applied migration 003_example_add_article_tags
```

### 4. Rollback If Needed
```bash
make db-rollback TARGET=002
# ✓ Rolled back migration 003_example_add_article_tags
```

## Safety Features

1. **Rollback file required**: Won't rollback without corresponding rollback file
2. **Dry run available**: See what would happen before executing
3. **Tracks changes**: Removes migration from tracking table
4. **Order matters**: Rolls back in reverse order
5. **Foreign key safe**: Example shows proper order for dropping tables

## Best Practices

1. **Always create rollback files** for structural changes
2. **Test rollbacks** in development first
3. **Use CASCADE carefully** - understand what gets deleted
4. **Data loss warning**: Rollbacks can delete data permanently
5. **Backup first** for production rollbacks

## Nuclear Option

If rollbacks fail, you can always:
```bash
make db-clean      # Destroys everything
make db-start      # Fresh database  
make db-migrate    # Rebuild from scratch
```