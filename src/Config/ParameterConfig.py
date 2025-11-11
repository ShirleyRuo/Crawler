import os

import json

from .Config import config
from ..utils.DataUnit import Parameters

class ParameterConfig:

    def __init__(self) -> None:
        self.parameter_path = config.config_dir / 'parameters.json'
    
    def _save_parameters(self) -> None:
        args = Parameters.__match_args__
        parameters = {
            'mode' : args[0],
            'function' : args[1],
            'block_id' : args[2],
            'from' : args[3],
            'sort_by' : args[4],
            '_' : args[5]
        }
        if os.path.exists(self.parameter_path):
            with open(self.parameter_path, 'r', encoding='utf-8') as f:
                old_parameters = json.load(f)
            if len(old_parameters) == len(parameters):
                return
        with open(self.parameter_path, 'w', encoding='utf-8') as f:
            json.dump(parameters, f, ensure_ascii=False, indent=4)
