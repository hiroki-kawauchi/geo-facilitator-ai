from dotenv import load_dotenv
import os
import sys
import vertexai
from vertexai.generative_models import (
    GenerationConfig,
    GenerativeModel,
    Content,
    Part,
    FunctionDeclaration,
    Tool,
    ToolConfig
)
from google.cloud import speech
import json
from shapely.geometry import Polygon
import geopandas as gpd
import pydeck as pdk

# コマンドライン引数の取得
args = sys.argv

# APIキーの取得
load_dotenv()
PROJECT_ID = os.getenv('GCP_PROJECT_ID')
LOCATION = os.getenv('GCP_LOCATION')
MODEL = os.getenv('MODEL')
audio_file_path = args[1]

# Vertex AIを初期化する
vertexai.init(project=PROJECT_ID, location=LOCATION)

def transcribe_audio(audio_file_path):
    client = speech.SpeechClient()

    with open(audio_file_path, 'rb') as audio_file:
        content = audio_file.read()

    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=48000,
        language_code="ja-JP",
    )

    response = client.recognize(config=config, audio=audio)

    if response.results:
        return response.results[0].alternatives[0].transcript
    else:
        return ""

# 音声認識
query = transcribe_audio(audio_file_path)
os.remove(audio_file_path)
print(query)

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

def buildbuilding(building_type='大きい', visualize=False):
    '''Build large or small buildings.'''

    if building_type == '大きい':
        param_buildingHeight = 150
        # ポリゴンの座標データ
        building_geojson= {
            "coordinates": [
                [
                    [360-220.2815894, 35.7307161],
                    [360-220.2813254, 35.7305787],
                    [360-220.281064, 35.7309219],
                    [360-220.2813187, 35.7310547],
                    [360-220.2815894, 35.7307161]
                ]
            ],
            "type": "Polygon"
        }

    elif building_type == '小さい':
        param_buildingHeight = 8
        building_geojson= {
          "coordinates": [
            [
              [360-220.281326,35.7308332],
              [360-220.2811964,35.7307622],
              [360-220.2810805,35.7309034],
              [360-220.2812083,35.7309759],
              [360-220.281326,35.7308332]
            ]
          ],
          "type": "Polygon"
        }

    # ShapelyのPolygonオブジェクトを作成
    polygon = Polygon(building_geojson['coordinates'][0])

    # GeoDataFrameの座標系を適切に設定 (ここではWGS84と仮定)
    building_gdf =  gpd.GeoDataFrame(index=[0], geometry=[polygon]).set_crs(epsg=4326)

    # 建物の高さをセット
    building_gdf['measuredHeight'] = param_buildingHeight

    if visualize:

      # ビューの設定
      view_state = pdk.ViewState(
          latitude=building_gdf.geometry.centroid.y.mean(),
          longitude=building_gdf.geometry.centroid.x.mean(),
          zoom=14,
          pitch=45,
      )

      # レイヤーの作成
      building_layer = pdk.Layer(
          "GeoJsonLayer",
          data=building_gdf,
          get_fill_color=[255,0, 0, 200],
          get_line_color=[0, 0, 0],
          get_line_width=5,
          pickable=True,
          extruded=True,
          get_elevation="setHeight",
      )

      # Deckインスタンスの作成と表示
      deck = pdk.Deck(layers=[building_layer], initial_view_state=view_state)
      deck.show()

    building_json = json.loads(building_gdf.to_json())
    save_json_to_directory(json_data=building_json, filename='building.json')
    return building_json

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

buildbuilding_func = FunctionDeclaration(
    name='buildbuilding',
    description='Build large or small buildings.',
    parameters={
        'type': 'object',
        'properties': {
            'building_type': {'type': 'string', 'description': 'Type of building to build, either "大きい" or "小さい".'},
            'visualize': {'type': 'boolean', 'description': 'Whether to visualize the building or not.'}
        },
    },
)

### Toolの定義
calc_tool = Tool(
  function_declarations=[add_func, multiply_func, buildbuilding_func]
)

### ToolConfigの定義
calc_tool_config = ToolConfig(
    function_calling_config=ToolConfig.FunctionCallingConfig(
        mode=ToolConfig.FunctionCallingConfig.Mode.ANY,
        allowed_function_names=['add_two_numbers', 'multiply_two_numbers', 'buildbuilding']
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

elif function_call.name == 'buildbuilding':

    # 引数の取り出し
    building_type = function_call.args.get('building_type', '大きい')
    visualize = function_call.args.get('visualize', False)

    # 関数の実行
    function_response = buildbuilding(building_type=building_type, visualize=visualize)

print(function_response)
