# mcs-ingest
Ingest data into Elasticsearch for MCS

# Example of ingesting a history file
python3 mcs_scene_ingest.py --folder ../generated_scenes/eval2/SCENE_HISTORY_OPICS/ --eval_name eval2_history --performer "OPICS (OSU, UU, NYU)" --type history --scene_folder ../generated_scenes/eval2/physics-scenes/

# Example of ingesting a scene file
python3 mcs_scene_ingest.py --folder ../generated_scenes/intphys_scenes/ --eval_name eval2_intphys_training --type scene