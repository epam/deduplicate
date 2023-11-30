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

import pandas as pd
from pandas import DataFrame

from utils.cleaning import clean_special_characters_from_data_frame


class QtestExcelDataLoader:
    def __init__(self, input_path: str, list_of_columns_to_check_for_nan: list[str],
                 column_name_needed_to_be_merged: str = 'Test Step Description',
                 test_case_id_column_name: str = 'Id',
                 sheet_name: str = 'Test Cases'):
        self.input_path = input_path
        self.list_of_columns_to_check_for_nan = list_of_columns_to_check_for_nan
        self.column_name_needed_to_be_merged = column_name_needed_to_be_merged
        self.test_case_id_column_name = test_case_id_column_name
        self.sheet_name = sheet_name

    def create_prepared_data_frame_from_excel_file(self) -> DataFrame:
        delimiter = '\n'
        initial_data_frame: DataFrame = pd.read_excel(
            self.input_path,
            sheet_name=self.sheet_name).dropna(
            subset=self.list_of_columns_to_check_for_nan,
            how='all')

        initial_data_frame.fillna("", inplace=True)

        joined_df: DataFrame = initial_data_frame.groupby(self.test_case_id_column_name)[
            self.column_name_needed_to_be_merged].apply(delimiter.join).reset_index()

        output_df: DataFrame = pd.merge(
            initial_data_frame.drop([self.column_name_needed_to_be_merged], axis=1).drop_duplicates(
                subset=self.test_case_id_column_name),
            joined_df, on=self.test_case_id_column_name).drop_duplicates(
            subset=self.test_case_id_column_name)

        # Removing \r and _x000D_ from all the output data frame values
        clean_special_characters_from_data_frame(output_df)

        return output_df
