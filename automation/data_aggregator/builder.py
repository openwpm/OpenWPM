from .base import BaseAggregator


def build_data_aggregator_class(manager_params):
    """
    Suggest renaming data_directory and s3_bucket
    to a consistent thing like "output_folder"
    and everything goes underneath it instead of
    maintaining different types of structures.
    "data_directory": "~/openwpm/",
    "s3_bucket" - "s3_directory"
      - can't see the point in having these be two inputs

    Not implemented
    "output_destination": "~/openwpm/"
    If S3 would be, for example, "openwpm-crawls/the_place_to_stick_the_data"

    "output_destination_type": "local",
    Options:
     - local (write to a local disk)
     - s3 (write to an s3 bucket)

    "output_structured_format": "sqlite",
    Options:
     - sqlite
     - parquet

    "output_unstructured_format": "leveldb",
    Options:
     - leveldb
     - gzip

    Current restrictions (in order that they will fall):
    - can't use parquet with local
    - can't use gzip with local
    - can't use sqlite with s3
    - can't use leveldb with s3
    """

    output_structured_format = manager_params["output_structured_format"]
    output_unstructured_format = manager_params["output_structured_format"]
    output_destination = manager_params["output_destination"]
    output_destination_type = manager_params["output_destination_type"]

    if output_structured_format == 'parquet' and output_destination_type == 'local':
        raise ValueError('Unsupported config.')
    if output_unstructured_format == 'gzip' and output_destination_type == 'local':
        raise ValueError('Unsupported config.')
    if output_structured_format == 'sqlite' and output_destination_type == 's3':
        raise ValueError('Unsupported config.')
    if output_unstructured_format == 'leveldb' and output_destination_type == 's3':
        raise ValueError('Unsupported config.')

    methods_dict = {}
    if output_structured_format == "sqlite":
        from .local import (
            __init__,
            _create_tables,
            _get_last_used_ids,
            save_configuration,
            get_next_visit_id,
            get_next_crawl_id,
            launch,
            shutdown
        )
        methods_dict = dict(
            __init__=__init__,
            _create_tables=_create_tables,
            _get_last_used_ids=_get_last_used_ids,
            save_configuration=save_configuration,
            get_next_visit_id=get_next_visit_id,
            get_next_crawl_id=get_next_crawl_id,
            launch=launch,
            shutdown=shutdown,
        )
    elif output_format == "s3":
        from .s3 import (
            __init__,
            _create_bucket,
            save_configuration,
            get_next_visit_id,
            get_next_crawl_id,
            launch,
        )
        methods_dict = dict(
            __init__=__init__,
            _create_bucket=_create_bucket,
            save_configuration=save_configuration,
            get_next_visit_id=get_next_visit_id,
            get_next_crawl_id=get_next_crawl_id,
            launch=launch,
        )
    else:
        raise Exception(f"Unrecognized output format: {output_format}")
    DataAggregator = type(
        'DataAggregator',
        (BaseAggregator, ),
        methods_dict,
    )
    return DataAggregator
