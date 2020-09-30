from pathlib import Path
from copy import deepcopy
import datetime as dt
import cProfile
import pstats
import json
import functools
import gc

from ipfx.dataset.create import create_ephys_data_set, create_ephys_data_set_lru
from ipfx.sweep_props import drop_tagged_sweeps
from ipfx.bin.run_qc import qc_summary
from ipfx.qc_feature_extractor import cell_qc_features, sweep_qc_features
from ipfx.qc_feature_evaluator import qc_experiment, DEFAULT_QC_CRITERIA_FILE
from ipfx.stimulus import StimulusOntology


with open(DEFAULT_QC_CRITERIA_FILE, "r") as path:
    QC_CRITERIA = json.load(path)

with open(StimulusOntology.DEFAULT_STIMULUS_ONTOLOGY_FILE, "r") \
        as path:
    ONTOLOGY = StimulusOntology(json.load(path))


def main(nwb_file, lru = False):
    if lru:
        print("testing LRU cache")
        data_set = create_ephys_data_set_lru(nwb_file=nwb_file, ontology=ONTOLOGY)
    else:
        print("testing no cache")
        data_set = create_ephys_data_set(nwb_file=nwb_file, ontology=ONTOLOGY)

    # cell QC worker
    cell_features, cell_tags = cell_qc_features(data_set)
    # cell_features = deepcopy(cell_features)

    # # sweep QC worker
    # sweep_features = sweep_qc_features(data_set)
    # sweep_features = deepcopy(sweep_features)
    # drop_tagged_sweeps(sweep_features)
    #
    # # experiment QC worker
    # cell_state, sweep_states = qc_experiment(
    #     ontology=ONTOLOGY,
    #     cell_features=cell_features,
    #     sweep_features=sweep_features,
    #     qc_criteria=QC_CRITERIA
    # )
    #
    # qc_summary(
    #     sweep_features=sweep_features,
    #     sweep_states=sweep_states,
    #     cell_features=cell_features,
    #     cell_state=cell_state
    # )


def clear_all_lru_cache():
    # All objects collected
    objects = [i for i in gc.get_objects()
               if isinstance(i, functools._lru_cache_wrapper)]

    # All objects cleared
    for object in objects:
        object.cache_clear()


if __name__ == '__main__':
    files = list(Path("data/nwb").glob("*.nwb"))
    base_dir = Path(__file__).parent
    today = dt.datetime.now().strftime('%y%m%d')

    now = dt.datetime.now().strftime('%H.%M.%S')
    profile_dir = base_dir.joinpath(f'profiles/{today}/{now}')
    profile_dir.mkdir(parents=True)
    for file in files:
        nwb_file = str(file)

        profile_file = str(profile_dir.joinpath(f'{str(file.stem)[0:10]}-cache1-cell.prof'))
        cProfile.run('main(nwb_file, lru=True)', filename=profile_file)
        p = pstats.Stats(profile_file)
        p.sort_stats('cumtime').print_stats(20)

        clear_all_lru_cache()

        profile_file = str(profile_dir.joinpath(f'{str(file.stem)[0:10]}-cache2-cell.prof'))
        cProfile.run('main(nwb_file, lru=False)', filename=profile_file)
        p = pstats.Stats(profile_file)
        p.sort_stats('cumtime').print_stats(20)

        clear_all_lru_cache()
