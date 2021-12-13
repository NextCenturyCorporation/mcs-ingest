import mcs_scene_ingest

def update_agency_scoring(client, db_string):
    mongoDB = client[db_string]
    history_collection = mongoDB["mcs_history"]
    agency_expected_records = history_collection.find({
        "eval": "Evaluation 4 Results", 
        "test_type": "agents", 
        "score.ground_truth": 1
    })

    for expected_record in agency_expected_records:
        unexpected_record = mcs_scene_ingest.return_agency_paired_history_item(
            client, db_string, expected_record)
        if unexpected_record is not None:
            mcs_scene_ingest.update_agency_scoring(expected_record, unexpected_record)
            mcs_scene_ingest.update_agency_paired_history_item(client, db_string, expected_record)
            mcs_scene_ingest.update_agency_paired_history_item(client, db_string, unexpected_record)
