#  Copyright (c) 2023 EPAM Systems
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#  https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License
import string
from typing import Optional
from gensim.parsing.preprocessing import strip_tags
from pandas import DataFrame
from ordered_set import OrderedSet
import os
import pandas as pd
import requests

PAGE_NUMBER = 1


class QTestApiDataLoader:

    def __init__(self, project_id: str, no_of_test_cases_per_page: int, module_id: Optional[str] = None):
        self.project_id = project_id
        self.no_of_test_cases_per_page = no_of_test_cases_per_page
        if module_id is not None:
            self.module_id = module_id

    def __prepare_request_endpoint(self, page_number: Optional[int] = None) -> tuple:
        url_str: str = f'https://ctcprod.qtestnet.com/api/v3/projects/{self.project_id}/test-cases'
        params = {
            'size': self.no_of_test_cases_per_page,
            'expandSteps': 'true'
        }

        if page_number is None:
            params['page'] = PAGE_NUMBER
        else:
            params['page'] = page_number

        if self.module_id is not None:
            params['parentId'] = self.module_id
        return url_str, params

    def fetch_test_cases_from_qtest_as_data_frame(self) -> DataFrame:
        request_headers: dict = {'Authorization': os.environ["BEARER_TOKEN"], 'content_type': 'application/json'}
        no_of_test_cases_returned_by_api_per_page = self.no_of_test_cases_per_page
        no_of_pages_counter = PAGE_NUMBER

        test_cases_data_frame: DataFrame = pd.DataFrame()

        while no_of_test_cases_returned_by_api_per_page == self.no_of_test_cases_per_page:
            request_endpoint_tuple: tuple = self.__prepare_request_endpoint(no_of_pages_counter)
            json_response = requests.get(url=request_endpoint_tuple[0], params=request_endpoint_tuple[1],
                                         headers=request_headers).json()

            no_of_test_cases_returned_by_api_per_page = len(json_response)
            if no_of_test_cases_returned_by_api_per_page < 1:
                break

            temp_data_frame: DataFrame = self.__transform_test_data_into_dict(json_response)
            test_cases_data_frame = test_cases_data_frame._append(temp_data_frame, ignore_index=True)
            no_of_pages_counter += 1

        return test_cases_data_frame

    @staticmethod
    def __transform_test_data_into_dict(json_response: list) -> DataFrame:
        fields_to_pick_from_api_response: list = ['name', 'pid', 'description', 'precondition', 'test_steps']
        api_data_dict: dict = {}
        data_frame: DataFrame = pd.DataFrame()

        for json_response_current_object in json_response:
            for key_name in json_response_current_object:
                current_key_data: str = json_response_current_object[key_name]
                if key_name in fields_to_pick_from_api_response:
                    if key_name == 'test_steps':
                        api_data_dict['Test Step Description'] = '\n'.join(map(str,
                                                                               [strip_tags(item['description'])
                                                                                for item in current_key_data
                                                                                for key in item
                                                                                if key == 'description']))
                        api_data_dict['Test Step Expected Result'] = '\n'.join(map(str,
                                                                                   OrderedSet(
                                                                                       [strip_tags(item['expected'])
                                                                                        for item in current_key_data
                                                                                        for key in item
                                                                                        if key == 'expected'])))
                    else:
                        if key_name == "description" or key_name == "precondition":
                            filtered_data: str = strip_tags(current_key_data)
                            if api_data_dict.get(key_name) is None:
                                api_data_dict[string.capwords(key_name)] = filtered_data
                            else:
                                if filtered_data not in api_data_dict[key_name]:
                                    api_data_dict[string.capwords(key_name)] = filtered_data
                        elif key_name == "pid":
                            api_data_dict['Id'] = current_key_data
                        else:
                            api_data_dict[string.capwords(key_name)] = current_key_data
            data_frame = data_frame._append(api_data_dict, ignore_index=True)
        return data_frame
