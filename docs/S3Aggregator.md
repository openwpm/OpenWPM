# Thoughts and observations regarding S3Aggregator.py

## How saving a record actually works

1. process_records writes to _records\[visit_id\]
2. _create_batch gets called once a certain visit_id is done
  and transforms all _records\[visit_id\] to a per-table batch which get appended
  to the _batches\[table_name\] list for a certain table
3. _send_to_s3 sends all data for a certain table if there are more
  than 500 batches for that table
  
## What this means for a visit_id that we want to mark as saved

A visit_id is only saved once all tables habe accumulated enough batches for it to be saved.
This means we would have to have a dict from visit_id to all tables it is contained in.
And a list of all visit_ids per batch so we know which entries in the other dict to remove.
