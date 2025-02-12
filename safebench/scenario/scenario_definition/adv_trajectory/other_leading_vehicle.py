''' 
Date: 2023-01-31 22:23:17
LastEditTime: 2023-03-01 16:53:14
Description: 
    Copyright (c) 2022-2023 Safebench Team

    This file is modified from <https://github.com/carla-simulator/scenario_runner/tree/master/srunner/scenarios>
    Copyright (c) 2018-2020 Intel Corporation

    This work is licensed under the terms of the MIT license.
    For a copy, see <https://opensource.org/licenses/MIT>
'''

import carla
import json

from safebench.scenario.tools.scenario_operation import ScenarioOperation
from safebench.scenario.tools.scenario_utils import calculate_distance_transforms
from safebench.scenario.scenario_manager.carla_data_provider import CarlaDataProvider
from safebench.scenario.tools.scenario_helper import get_waypoint_in_distance
from safebench.scenario.scenario_definition.basic_scenario import BasicScenario


class OtherLeadingVehicle(BasicScenario):

    """
    This class holds everything required for a simple "Other Leading Vehicle"
    scenario involving a user controlled vehicle and two other actors.
    Traffic Scenario 05

    This is a single ego vehicle scenario
    """

    def __init__(self, world, ego_vehicles, config, randomize=False, debug_mode=False, criteria_enable=True,
                 timeout=80):
        """
        Setup all relevant parameters and create scenario
        """
        self._world = world
        self._map = CarlaDataProvider.get_map()
        self._first_vehicle_location = 35
        self._second_vehicle_location = self._first_vehicle_location + 1
        self._ego_vehicle_drive_distance = self._first_vehicle_location * 4
        self._first_vehicle_speed = 12
        self._second_vehicle_speed = 12
        self._reference_waypoint = self._map.get_waypoint(config.trigger_points[0].location)
        self._other_actor_max_brake = 1.0
        self._first_actor_transform = None
        self._second_actor_transform = None
        # Timeout of scenario in seconds
        self.timeout = timeout

        self.dece_distance = 2
        self.dece_target_speed = 3  # 3 will be safe

        self.need_decelerate = False

        super(OtherLeadingVehicle, self).__init__("VehicleDeceleratingInMultiLaneSetUpDynamic",
                                                  ego_vehicles,
                                                  config,
                                                  world,
                                                  debug_mode,
                                                  criteria_enable=criteria_enable)

        self.scenario_operation = ScenarioOperation(self.ego_vehicles, self.other_actors)
        self.actor_type_list.append('vehicle.nissan.patrol')
        self.actor_type_list.append('vehicle.audi.tt')
        self.trigger_distance_threshold = 35
        self.other_actor_speed = []
        self.other_actor_speed.append(self._first_vehicle_speed)
        self.other_actor_speed.append(self._second_vehicle_speed)
        self.ego_max_driven_distance = 200

        self.step = 0
        with open(config.parameters, 'r') as f:
            parameters = json.load(f)
        self.control_seq = [(control * 2 - 1) * 2 for control in parameters]
        self.total_steps = len(self.control_seq)
        self.actor_transform_list = []
        self.perturbed_actor_transform_list = []
        self.running_distance = 50

    def initialize_actors(self):
        first_vehicle_waypoint, _ = get_waypoint_in_distance(self._reference_waypoint, self._first_vehicle_location)
        second_vehicle_waypoint, _ = get_waypoint_in_distance(self._reference_waypoint, self._second_vehicle_location)
        second_vehicle_waypoint = second_vehicle_waypoint.get_left_lane()
        first_vehicle_transform = carla.Transform(first_vehicle_waypoint.transform.location,
                                                  first_vehicle_waypoint.transform.rotation)
        second_vehicle_transform = carla.Transform(second_vehicle_waypoint.transform.location,
                                                   second_vehicle_waypoint.transform.rotation)

        self.other_actor_transform.append(first_vehicle_transform)
        self.other_actor_transform.append(second_vehicle_transform)
        self.scenario_operation.initialize_vehicle_actors(self.other_actor_transform, self.other_actors, self.actor_type_list)
        # self.reference_actor = self.other_actors[1]
        self.reference_actor = self.other_actors[0]

        self._first_actor_transform = first_vehicle_transform
        self.second_vehicle_transform = carla.Transform(second_vehicle_waypoint.transform.location,
                                                       second_vehicle_waypoint.transform.rotation)

        forward_vector = self._first_actor_transform.rotation.get_forward_vector() * self.running_distance
        right_vector = self._first_actor_transform.rotation.get_right_vector()
        self.other_actor_final_transform = carla.Transform(
            self._first_actor_transform.location,
            self._first_actor_transform.rotation)
        self.other_actor_final_transform.location += forward_vector
        for i in range(self.total_steps):
            self.actor_transform_list.append(carla.Transform(
                carla.Location(self._first_actor_transform.location + forward_vector * i / self.total_steps),
                self._first_actor_transform.rotation))
        for i in range(self.total_steps):
            self.perturbed_actor_transform_list.append(carla.Transform(
                carla.Location(self.actor_transform_list[i].location + right_vector * self.control_seq[i]),
                self._first_actor_transform.rotation))

        # print('other_actor_transform')
        # for i in self.other_actor_transform:
        #     print(i)
        # print('perturbed_actor_transform_list')
        # for i in self.perturbed_actor_transform_list:
        #     print(i)

    def update_behavior(self):
        """
        Just make two vehicles move forward with specific speed
        At specific point, vehicle in front of ego will decelerate
        other_actors[0] is the vehicle before the ego
        """
        # cur_distance = calculate_distance_transforms(CarlaDataProvider.get_transform(self.ego_vehicles[0]),
        #                                              CarlaDataProvider.get_transform(self.other_actors[1]))
        cur_distance = calculate_distance_transforms(self.other_actor_transform[0], CarlaDataProvider.get_transform(self.other_actors[0]))

        if cur_distance > self.dece_distance:
            self.need_decelerate = True
        for i in range(len(self.other_actors)):
            if i == 0 and self.need_decelerate:
                # print(self.step)
                target_transform = self.perturbed_actor_transform_list[self.step if self.step < self.total_steps else -1]
                self.step += 1  # max 100
                self.scenario_operation.drive_to_target_followlane(i, target_transform, self.dece_target_speed)
            else:
                self.scenario_operation.go_straight(self.other_actor_speed[i], i, throttle_value=2.0)

    def _create_behavior(self):
        pass

    def check_stop_condition(self):
        pass
