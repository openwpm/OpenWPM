
def commit_unstructured_records(self):
    # We commit every time so there's no batches to do
    pass

def process_content(self, record):
    """Upload page content `record` to S3"""
    if record[0] != RECORD_TYPE_CONTENT:
        raise ValueError(
            "Incorrect record type passed to `process_content`. Expected "
            "record of type `%s`, received `%s`." % (
                RECORD_TYPE_CONTENT, record[0])
        )
    content, content_hash = record[1]
    content = base64.b64decode(content)
    fname = "%s/%s/%s.gz" % (self.dir, CONTENT_DIRECTORY, content_hash)
    self._write_str_to_s3(content, fname)

# WHERE AND WHAT SHOULD BE SEPARATE

def _write_str_to_s3(self, string, filename,
                        compressed=True, skip_if_exists=True):
    """Write `string` data to S3 with name `filename`"""
    if skip_if_exists and self._exists_on_s3(filename):
        self.logger.debug(
            "File `%s` already exists on s3, skipping..." % filename)
        return
    if not isinstance(string, bytes):
        string = string.encode('utf-8')
    if compressed:
        out_f = io.BytesIO()
        with gzip.GzipFile(fileobj=out_f, mode='w') as writer:
            writer.write(string)
        out_f.seek(0)
    else:
        out_f = io.BytesIO(string)

    # Upload to S3
    try:
        self._s3.upload_fileobj(out_f, self._bucket, filename)
        self.logger.debug(
            "Successfully uploaded file `%s` to S3." % filename)
        # Cache the filenames that are already on S3
        # We strip the bucket name as its the same for all files
        if skip_if_exists:
            self._s3_content_cache.add(filename.split('/', 1)[1])
    except Exception:
        self.logger.error(
            "Exception while uploading %s" % filename, exc_info=True
        )
        pass