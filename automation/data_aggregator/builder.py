from .base import BaseAggregator


def build_data_aggregator_class(manager_params):
    output_format = manager_params["output_format"]
    methods_dict = {}
    if output_format == "local":
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
