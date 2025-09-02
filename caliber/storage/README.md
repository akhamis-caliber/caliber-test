# Storage Directory

This directory contains uploaded files and generated reports for the Caliber application.

## Directory Structure

```
storage/
├── {org_id}/              # Organization-specific directory
│   ├── {report_id}/       # Report-specific directory
│   │   ├── original.csv   # Original uploaded file
│   │   ├── scores.csv     # Processed scores
│   │   └── summary.json   # Processing summary
│   └── exports/           # Generated exports
└── temp/                  # Temporary files
```

## File Management

- **Original Files**: Stored in `{org_id}/{report_id}/` with original filename
- **Processed Results**: Stored as `scores.csv` and `summary.json`
- **Exports**: Generated on-demand and stored in `exports/` subdirectory
- **Cleanup**: Old files are cleaned up by periodic Celery tasks

## Storage Configuration

The storage root path is configured via the `STORAGE_ROOT` environment variable.
Default: `/app/storage`

## Local Development

In local development, files are stored on the local filesystem.
In production, this can be configured to use cloud storage (S3, GCS, etc.).