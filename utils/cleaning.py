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

import re
import string

from openpyxl.utils import escape
from pandas import DataFrame

# Custom keywords to be removed from the document
custom_kw = ["change", "processing", "verify", "check"]


# Function to extract needed columns from Data Frame and prepare them for further usage
def clean_data_frame(data_frame: DataFrame, columns: list[str]) -> list[str]:
    data_frame: DataFrame = data_frame[columns].apply(lambda value: '\n'.join(value.astype(str)).lower(), axis=1)
    list_of_vals: list[str] = data_frame.tolist()

    list_of_vals: list[str] = [re.sub("\d+", " ", document) for document in list_of_vals]
    list_of_vals: list[str] = [" ".join([w for w in document.split() if len(w) > 1]) for document in list_of_vals]
    list_of_vals: list[str] = ["".join(
        [char.lower() for char in document if char not in string.punctuation]
    ) for document in list_of_vals]
    list_of_vals: list[str] = [re.sub("\W+", " ", document) for document in list_of_vals]
    # Don't need to do the cleaning of stop words since they have an influence on the meaning of the sentences from testing perspective
    # list_of_vals: list[str] = [remove_stopwords(document) for document in list_of_vals]
    for kw in custom_kw:
        list_of_vals: list[str] = [document.replace(kw, "") for document in list_of_vals]
    return list_of_vals


# Function to cleanse document
def cleanse_document(document, columns):
    document = '\n'.join([document[column.strip()].lower() for column in columns])

    # remove numbers
    document = re.sub("\d+", " ", document)

    # print("\n",document)
    # remove single characters
    document = " ".join([w for w in document.split() if len(w) > 1])
    # print("--- join ",document)

    # remove punctuations and convert characters to lower case
    document = "".join(
        [char.lower() for char in document if char not in string.punctuation]
    )

    # Remove all non-alphanumeric characters
    document = re.sub("\W+", " ", document)

    # Remove 'out of the box' stopwords
    # Don't need to do the cleaning of stop words since they have an influence on the meaning of the sentences from testing perspective
    # document = remove_stopwords(document)
    # print("--- rem ",document)

    # Remove custom keywords
    for kw in custom_kw:
        document = document.replace(kw, "")

    return document


# Function to clean the Data Frame from special characters, which may come from excel documents
def clean_special_characters_from_data_frame(data_frame: DataFrame):
    for str_col in data_frame.select_dtypes(include=['object']).columns:
        data_frame[str_col] = data_frame[str_col].astype(str).apply(escape.unescape)
