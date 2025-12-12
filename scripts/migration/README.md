# Data Migration Scripts

Scripts for migrating data from me-central-1 to us-east-1 region.

## Scripts

### export_data.py
Exports DynamoDB tables and S3 objects from the source region.

```bash
export SOURCE_REGION=me-central-1
export SOURCE_BUCKET=otc-menat-2025
export EXPORT_DIR=/tmp/migration_export

python scripts/migration/export_data.py
```

### import_data.py
Imports data to the target region after transformation.

```bash
export TARGET_REGION=us-east-1
export TARGET_BUCKET=trade-matching-us-east-1
export IMPORT_DIR=/tmp/migration_export

python scripts/migration/import_data.py
```

### validate_migration.py
Validates data migration between regions.

```bash
export SOURCE_REGION=me-central-1
export TARGET_REGION=us-east-1

python scripts/migration/validate_migration.py
```

## Migration Steps

1. **Export**: Run `export_data.py` to export all data from me-central-1
2. **Review**: Check `export_verification.json` for export summary
3. **Import**: Run `import_data.py` to import data to us-east-1
4. **Validate**: Run `validate_migration.py` to verify migration
5. **Test**: Run integration tests against the new region

## Data Transformations

- S3 bucket references are updated from source to target bucket
- Migration metadata is added to each record
- Region references in configuration are updated

## Rollback

If migration fails, the source data remains unchanged. Simply update
environment variables to point back to me-central-1.
