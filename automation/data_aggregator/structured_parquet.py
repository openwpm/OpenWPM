

def handle_create(self, data):
    # Nothing to do for parquet
    pass


def write_structured_data(self, table, data, visit_id):
    """Insert data into a RecordBatch"""
    # Convert data to text type
    for k, v in data.items():
        if isinstance(v, bytes):
            data[k] = str(v, errors='ignore')
        elif callable(v):
            data[k] = str(v)
        # TODO: Can we fix this in the extension?
        elif type(v) == dict:
            data[k] = json.dumps(v)

    records = self._records[visit_id]
    # Add nulls
    for item in PQ_SCHEMAS[table].names:
        if item not in data:
            data[item] = None
    # Add instance_id (for partitioning)
    data['instance_id'] = self._instance_id
    records[table].append(data)


# SHOULD BE SEPARATE FROM S3

def commit_structured_records(self, force=False):
    """Write in-memory batches to s3"""
    should_send = force
    for batches in self._batches.values():
        if len(batches) > CACHE_SIZE:
            should_send = True
    if not should_send:
        return

    for table_name, batches in self._batches.items():
        if table_name == SITE_VISITS_INDEX:
            out_str = '\n'.join([json.dumps(x) for x in batches])
            out_str = out_str.encode('utf-8')
            fname = '%s/site_index/instance-%s-%s.json.gz' % (
                self.dir, self._instance_id,
                hashlib.md5(out_str).hexdigest()
            )
            self._write_str_to_s3(out_str, fname)
        else:
            if len(batches) == 0:
                continue
            try:
                table = pa.Table.from_batches(batches)
                pq.write_to_dataset(
                    table, self._s3_bucket_uri % table_name,
                    filesystem=self._fs,
                    partition_cols=['instance_id'],
                    compression='snappy',
                    flavor='spark'
                )
            except (pa.lib.ArrowInvalid, EndpointConnectionError):
                self.logger.error(
                    "Error while sending records for: %s" % table_name,
                    exc_info=True
                )
                pass
        # can't del here because that would modify batches
        self._batches[table_name] = list()
    for visit_id in self._unsaved_visit_ids:
        self.mark_visit_complete(visit_id)
    self._unsaved_visit_ids = set()

def init_structured_datasource(self):
    def factory_function():
        return defaultdict(list)

    self._records: Dict[int, DefaultDict[str, List[Any]]] =\
        defaultdict(factory_function)  # maps visit_id and table to records
    self._batches: DefaultDict[str, List[pa.RecordBatch]] = \
        defaultdict(list)  # maps table_name to a list of batches
    self._unsaved_visit_ids: MutableSet[int] = \
        set()
    self._instance_id = instance_id


def shutdown_structured_datasource(self):
    # nothing to do
    pass