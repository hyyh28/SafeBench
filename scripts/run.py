''' 
Date: 2023-01-31 22:23:17
LastEditTime: 2023-03-07 13:06:41
Description: 
'''

import traceback
import os.path as osp

import torch 

from safebench.util.run_util import load_config
from safebench.util.torch_util import set_seed, set_torch_variable
from safebench.carla_runner import CarlaRunner
from safebench.scenic_runner import ScenicRunner


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--exp_name', type=str, default='exp')
    parser.add_argument('--output_dir', type=str, default='log')
    parser.add_argument('--ROOT_DIR', type=str, default=osp.abspath(osp.dirname(osp.dirname(osp.realpath(__file__)))))

    parser.add_argument('--max_episode_step', type=int, default=300)
    parser.add_argument('--auto_ego', action='store_true')
    parser.add_argument('--mode', '-m', type=str, default='eval', choices=['train_agent', 'train_scenario', 'eval'])
    parser.add_argument('--agent_cfg', type=str, default='dummy.yaml')
    parser.add_argument('--scenario_cfg', type=str, default='standard.yaml')
    parser.add_argument('--continue_agent_training', '-cat', type=bool, default=False)
    parser.add_argument('--continue_scenario_training', '-cst', type=bool, default=False)

    parser.add_argument('--seed', '-s', type=int, default=0)
    parser.add_argument('--threads', type=int, default=4)
    parser.add_argument('--device', type=str, default='cuda:0' if torch.cuda.is_available() else 'cpu')   

    parser.add_argument('--num_scenario', '-ns', type=int, default=2, help='num of scenarios we run in one episode')
    parser.add_argument('--save_video', action='store_true')
    parser.add_argument('--render', type=bool, default=True)
    parser.add_argument('--frame_skip', '-fs', type=int, default=1, help='skip of frame in each step')
    parser.add_argument('--port', type=int, default=2000, help='port to communicate with carla')
    parser.add_argument('--tm_port', type=int, default=8000, help='traffic manager port')
    parser.add_argument('--fixed_delta_seconds', type=float, default=0.1)
    args = parser.parse_args()
    args_dict = vars(args)

    # set global parameters
    set_torch_variable(args.device)
    torch.set_num_threads(args.threads)
    set_seed(args.seed)

    # load agent config
    agent_config_path = osp.join(args.ROOT_DIR, 'safebench/agent/config', args.agent_cfg)
    agent_config = load_config(agent_config_path)

    # load scenario config
    scenario_config_path = osp.join(args.ROOT_DIR, 'safebench/scenario/config', args.scenario_cfg)
    scenario_config = load_config(scenario_config_path)

    # main entry with a selected mode
    agent_config.update(args_dict)
    scenario_config.update(args_dict)
    if scenario_config['type_category'] == 'scenic':
        assert scenario_config['num_scenario'] == 1, 'the num_scenario can only be one for scenic now'
        runner = ScenicRunner(agent_config, scenario_config)
    else:
        runner = CarlaRunner(agent_config, scenario_config)
    
    # start running
    try:
        runner.run()
    except:
        runner.close()
        traceback.print_exc()
