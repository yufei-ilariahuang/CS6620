<!-- Midterm implementation notes and deployment guide. -->

# Midterm Object Backup System

This folder contains a complete CDK implementation of the object backup system.

## Stacks

1. `MidtermStorageStack`
- Creates `Bucket Src` and `Bucket Dst`.
- Creates DynamoDB `Table T`.

2. `MidtermReplicatorStack`
- Creates Replicator Lambda.
- Subscribes Replicator to S3 create/delete events from `Bucket Src`.

3. `MidtermCleanerStack`
- Creates Cleaner Lambda.
- Schedules Cleaner every 1 minute (EventBridge rule).

## Table T Design (No Scan Required)

Base table:
- Partition key: `source_key` (original object key)
- Sort key: `copy_sort` (timestamp-based sortable id)

Attributes:
- `copy_key`: object key in destination bucket
- `created_at`: copy creation epoch seconds
- `copy_status`: `OWNED` or `DISOWNED`
- `disowned_at`: epoch seconds when marked disowned (`0` while owned)

GSI:
- Name: `status-disowned-at-index`
- Partition key: `copy_status`
- Sort key: `disowned_at`

How queries work without scan:
- Replicator (PUT/DELETE paths) queries by `source_key` in base table.
- Cleaner queries disowned and expired copies by GSI where:
  - `copy_status = DISOWNED`
  - `disowned_at <= now - 10`

## Lambda Behavior

Replicator (`lambda/replicator_lambda.py`):
- On PUT:
  1. Copy source object to destination bucket with a generated copy key.
  2. Insert mapping row into Table T as `OWNED`.
  3. Query current owned copies for this source object.
  4. If more than 3 copies exist, delete oldest extras from S3 and remove their rows from Table T.

- On DELETE:
  1. Query owned copies for the source object.
  2. Mark them as `DISOWNED` and set `disowned_at = now`.
  3. Do not delete S3 copies here.

Cleaner (`lambda/cleaner_lambda.py`):
- Runs every minute.
- Queries GSI for disowned copies older than 10 seconds.
- Deletes those objects from destination bucket.
- Deletes corresponding rows from Table T so future queries do not return them.

## Files Added

- `app.py`
- `cdk/storage_stack.py`
- `cdk/replicator_stack.py`
- `cdk/cleaner_stack.py`
- `lambda/replicator_lambda.py`
- `lambda/cleaner_lambda.py`
- `requirements.txt`
- `cdk.json`

## Deploy

1. Create and activate a Python virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Bootstrap CDK if needed:

```bash
cdk bootstrap
```

4. Deploy:

```bash
cdk deploy --all
```

## Quick Test

1. Upload the same object key to source bucket multiple times.
2. Verify destination bucket keeps only the 3 most recent copies for that source key.
3. Delete the original object from source bucket.
4. Wait at least 10 seconds.
5. Wait for Cleaner schedule (up to 1 minute) and verify disowned copies are removed from destination bucket and table.