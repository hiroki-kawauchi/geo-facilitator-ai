import json
import os
import sys

import geopandas as gpd
import pandas as pd
import pydeck as pdk
import requests
import vertexai
from dotenv import load_dotenv
from plateaukit import load_dataset
from shapely.geometry import Point, Polygon
from vertexai.generative_models import (
    Content,
    FunctionDeclaration,
    GenerationConfig,
    GenerativeModel,
    Part,
    Tool,
    ToolConfig,
)

# コマンドライン引数の取得
args = sys.argv

# APIキーの取得
load_dotenv()
PROJECT_ID = os.getenv('GCP_PROJECT_ID')
LOCATION = os.getenv('GCP_LOCATION')
MODEL = os.getenv('MODEL')

### Vertex AIを初期化する
vertexai.init(project=PROJECT_ID, location=LOCATION)

# コマンドライン引数からクエリを取得
query = args[1]

### 関数の実装
def add_two_numbers(a: int, b: int):
    return a + b

def multiply_two_numbers(a: int, b: int):
    return a * b

def save_json_to_directory(json_data, filename, output_path='../public/'):
    # ディレクトリが存在しない場合は作成する
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    
    # JSONデータをファイルに保存する
    file_path = os.path.join(output_path, filename)
    with open(file_path, 'w') as file:
        json.dump(json_data, file, indent=2, ensure_ascii=False)

def show_flood_depth(show_type='浸水深表示', visualize=False):
    '''Show flood depth of the designated area.'''

    if show_type == '浸水深表示':
        param_floodingDepth = 70
        # ポリゴンの座標データ
        flooding_geojson= {
            "coordinates": [
                [
                    [139.520678, 35.649120],
                    [139.525356, 35.642930],
                    [139.548423, 35.636177],
                    [139.552220, 35.646052],
                    [139.528872, 35.655039],
                    [139.520678, 35.649120]
                ]
            ],
            "type": "Polygon"
        }

    elif show_type == '浸水深削除':
        param_floodingDepth = 0
        flooding_geojson= {
          "coordinates": [
                [
                    [139.520678, 35.649120],
                    [139.525356, 35.642930],
                    [139.548423, 35.636177],
                    [139.552220, 35.646052],
                    [139.528872, 35.655039],
                    [139.520678, 35.649120]
                ]
          ],
          "type": "Polygon"
        }

    # ShapelyのPolygonオブジェクトを作成
    polygon = Polygon(flooding_geojson['coordinates'][0])

    # GeoDataFrameの座標系を適切に設定 (ここではWGS84と仮定)
    flooding_gdf =  gpd.GeoDataFrame(index=[0], geometry=[polygon]).set_crs(epsg=4326)

    # 浸水深をセット
    flooding_gdf['measuredHeight'] = param_floodingDepth
    flooding_json = json.loads(flooding_gdf.to_json())
    save_json_to_directory(json_data=flooding_json, filename='flooding.json')
    return flooding_json

def show_shelters(show_type='避難所表示', visualize=False):
    '''Show shelters.'''
    # 2つのPointを作成
    point1 = Point(139.537108, 35.648013)  # Example: Tokyo, Japan
    point2 = Point(139.527570, 35.654551)  # Example: New York City, USA

    # GeoDataFrameを作成
    shelters_gdf = gpd.GeoDataFrame([{'geometry': point1,}, 
                            {'geometry': point2,}],
                        crs="EPSG:4326")

    
    shelters_json = json.loads(shelters_gdf.to_json())
    save_json_to_directory(json_data=shelters_json, filename='shelters.json')
    return shelters_json

### 関数宣言
add_func = FunctionDeclaration(
    name='add_two_numbers',
    description='Add two numbers.',
    parameters={
        'type': 'object',
        'properties': {'a': {'type': 'integer', 'description': 'one number'}, 'b': {'type': 'integer', 'description': 'another number'}},
    },
)

multiply_func = FunctionDeclaration(
    name='multiply_two_numbers',
    description='Multiply two numbers.',
    parameters={
        'type': 'object',
        'properties': {'a': {'type': 'integer', 'description': 'one number'}, 'b': {'type': 'integer', 'description': 'another number'}},
    },
)

show_flood_depth_func = FunctionDeclaration(
    name='show_flood_depth',
    description='Show flood depth of the designated area.',
    parameters={
        'type': 'object',
        'properties': {
            'show_type': {'type': 'string', 'description': 'Either "浸水深表示" or "浸水深削除".'}
        },
    },
)

show_shelters_func = FunctionDeclaration(
    name='show_shelters',
    description='Show shelters.',
    parameters={
        'type': 'object',
        'properties': {
            'show_type': {'type': 'string', 'description': '避難所（shelters）を表示します。'}
        },
    },
)

### Toolの定義
calc_tool = Tool(
  function_declarations=[add_func, multiply_func, show_flood_depth_func, show_shelters_func]
)

### ToolConfigの定義
calc_tool_config = ToolConfig(
    function_calling_config=ToolConfig.FunctionCallingConfig(
        mode=ToolConfig.FunctionCallingConfig.Mode.ANY,
        allowed_function_names=['add_two_numbers', 'multiply_two_numbers', 'show_flood_depth', 'show_shelters']
    )
)

### モデルの定義
model = GenerativeModel(
    model_name=MODEL,
    tools=[calc_tool],
    tool_config=calc_tool_config
)

### ユーザープロンプトの定義
user_prompt_content = Content(
    role='user',
    parts=[
        Part.from_text(query)
    ]
)

### 呼び出す関数と引数をモデルに生成させる
response = model.generate_content(
    user_prompt_content,
)
response_function_call_content = response.candidates[0].content
function_call = response.candidates[0].content.parts[0].function_call

### 関数を実行する
function_response = None
if function_call.name == 'add_two_numbers':

    # 引数の取り出し
    a = function_call.args['a']
    b = function_call.args['b']

    # 関数の実行
    function_response = add_two_numbers(a=a, b=b)

elif function_call.name == 'multiply_two_numbers':

    # 引数の取り出し
    a = function_call.args['a']
    b = function_call.args['b']

    # 関数の実行
    function_response = multiply_two_numbers(a=a, b=b)

elif function_call.name == 'show_flood_depth':

    # 引数の取り出し
    show_type = function_call.args.get('show_type', '浸水深表示')

    # 関数の実行
    function_response = show_flood_depth(show_type=show_type)

elif function_call.name == 'show_shelters':
    # 引数の取り出し
    show_type = function_call.args.get('show_type', '避難所表示')

    # 関数の実行
    function_response = show_shelters(show_type=show_type)

print(function_response)
