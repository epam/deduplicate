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

import tempfile
from json import loads
from os import path, environ
from traceback import format_exc

import gradio as gr
import pandas as pd
from pandas import DataFrame
from sentence_transformers import SentenceTransformer, util
from torch import Tensor

from dataloaders.qtest_excel import QtestExcelDataLoader
from utils.stringdiff import equalize
from utils.cleaning import clean_data_frame, cleanse_document, clean_special_characters_from_data_frame


def calculate_similarity(data_source, is_raw_data: bool, excel_sheet_name: str, encoding: str, delimiter: str,
                         idcol: str, columns: str,
                         cutoff: float = 0.8,
                         test_steps: str = ''):
    try:
        delimiter = delimiter.replace("\\t", "\t").strip()
        try:
            test_steps = loads(test_steps)
        except:
            test_steps = ''

        cols: list[str] = columns.split(delimiter)

        if is_raw_data:
            data_loader = QtestExcelDataLoader(data_source.name, ['Precondition', 'Test Step Description',
                                                                  'Test Step Expected Result'],
                                               sheet_name=excel_sheet_name, test_case_id_column_name=idcol)
            initial_data: DataFrame = data_loader.create_prepared_data_frame_from_excel_file()
        else:
            if data_source.name.__contains__('csv'):
                initial_data: DataFrame = pd.read_csv(data_source.name, encoding=encoding)
            else:
                initial_data: DataFrame = pd.read_excel(data_source.name, sheet_name=excel_sheet_name)
                initial_data.fillna("", inplace=True)

        prepared_data_list: list[str] = clean_data_frame(initial_data, cols)

        model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2',
                                    device='cpu', cache_folder="./models_cache")

        # Compute embeddings
        embeddings: Tensor = model.encode(prepared_data_list, convert_to_tensor=True)
        if not test_steps:
            cosine_scores: Tensor = util.cos_sim(embeddings, embeddings)
        else:
            steps_embeddings: Tensor = model.encode([cleanse_document(test_steps, cols)], convert_to_tensor=True)
            cosine_scores = util.semantic_search(steps_embeddings, embeddings, score_function=util.dot_score, top_k=5)
        result_data_frame = DataFrame()
        if not test_steps:
            for (index, scores) in enumerate(cosine_scores):
                for (jindex, score) in enumerate(scores):
                    if score > cutoff and index < jindex:
                        record = {
                            f'{idcol} #1': initial_data.at[index, idcol],
                            f'{idcol} #2': initial_data.at[jindex, idcol],
                            'Score': round(score.item(), 3)
                        }
                        composite_score = 0
                        for col in cols:
                            data_at_index: str = cleanse_document({col: initial_data.at[index, col]}, [col])
                            composite_score += util.cos_sim(
                                model.encode([data_at_index]),
                                model.encode([cleanse_document({col: initial_data.at[jindex, col]}, [col])])
                            )
                        composite_score /= len(cols)
                        record['Composite Score'] = round(composite_score.item(), 3)
                        for col in initial_data.columns:
                            if col != idcol:
                                if col in cols:
                                    (col1, col2) = equalize(initial_data.at[index, col], initial_data.at[jindex, col])
                                    record[f'{col} #1'] = col1
                                    record[f'{col} #2'] = col2
                                else:
                                    record[f'{col} #1'] = initial_data.at[index, col]
                                    record[f'{col} #2'] = initial_data.at[jindex, col]
                        result_data_frame = result_data_frame._append(record, ignore_index=True)
        else:
            for issues in cosine_scores:
                for issue in issues:
                    if issue['score'] >= cutoff:
                        record = {'Score': round(issue['score'], 3)}
                        for col in initial_data[issue['corpus_id']].keys():
                            if col in cols:
                                (col1, col2) = equalize(test_steps[col], initial_data.at[issue['corpus_id'], col])
                                record[f'{col} #1'] = col1
                                record[f'{col} #2'] = col2
                            else:
                                record[f'{col} #1'] = test_steps.get(col, '')
                                record[f'{col} #2'] = initial_data.at[issue['corpus_id'], col]
                        result_data_frame = result_data_frame._append(record, ignore_index=True)
        out_path = path.join(tempfile.gettempdir(), "duplicates.xlsx")
        if result_data_frame.empty is False:
            if test_steps:
                result_data_frame.sort_values('Score', ascending=False, inplace=True)
            else:
                result_data_frame.sort_values(['Score', 'Composite Score'], ascending=[False, False], inplace=True)
            clean_special_characters_from_data_frame(result_data_frame)
            result_data_frame.to_excel(out_path, sheet_name='Deduplication Result', index=False)
        else:
            out_path = None
        return [f'Identified {len(result_data_frame)} pairs of potential duplicates', out_path]
    except Exception as e:
        return [f'Error: {format_exc()}', None]


def main():
    iface = gr.Interface(
        fn=calculate_similarity, inputs=[
            gr.components.File(label="Test cases is csv or xlsx or xls format", type="file",
                               file_types=['csv', 'xlsx', 'xls']),
            gr.components.Checkbox(label="Indicate that raw data will be using", value=False,
                                   info='Used only for unprepared data sheets in excel imported from qTest'),
            gr.components.Textbox(lines=1,
                                  label="Excel sheet name for deduplication from excel document",
                                  info='Required when you do deduplication based on xlsx file'),
            gr.components.Dropdown(["utf-8", "utf-8-sig", "latin-1", "cp1252"], value='utf-8', label="Encoding",
                                   info="Encoding of your file may be very different from UTF-8. For csv only"),
            gr.components.Textbox(lines=1, value=',', label="Columns delimiter"),
            gr.components.Textbox(lines=1, label="Column name with entity ID"),
            gr.components.Textbox(lines=1,
                                  label="Delimiter separated list of columns to be used for duplicates detection"),
            gr.components.Slider(0, 1, value=0.8, step=0.01, label="Cut-off score"),
            gr.components.Textbox(lines=5, label="Test case for deduplication"),
        ],
        outputs=[
            "text",
            gr.components.File(label="Generated file with duplicates", type="file", file_types=['xlsx']),
        ], title="Deduplication of entities")
    iface.launch(share=False, server_name="0.0.0.0", server_port=environ.get("DEDUPE_PORT", 8899))


if __name__ == '__main__':
    main()
