from langchain_core.tools import tool
from plateaukit import load_dataset
from dotenv import load_dotenv
from shapely.geometry import Polygon
import pydeck as pdk
import osmnx as ox
import networkx as nx
import geopandas as gpd
import pandas as pd
import json
import requests
import os


### JSONを指定のディレクトリへ保存するツール
def save_json_to_directory(json_data, filename, output_path='../public/'):
    # ディレクトリが存在しない場合は作成する
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    
    # JSONデータをファイルに保存する
    file_path = os.path.join(output_path, filename)
    with open(file_path, 'w') as file:
        json.dump(json_data, file, indent=2, ensure_ascii=False)
    
    # print(f"JSONファイルが {file_path} に保存されました。")


### 建物選択ツール
@tool
def getbuilding_by_name(building_name, visualize=False):
    '''Retrieve building information by building name'''
    tokyo23ku = load_dataset("plateau-tokyo23ku-2022.cloud")
    area = tokyo23ku.area_from_landmark(building_name)
    basemap_gdf = area.gdf
    building_gdf =  basemap_gdf.query("name == @building_name")

    if visualize:

      # ビューの設定
      view_state = pdk.ViewState(
          latitude=basemap_gdf.geometry.centroid.y.mean(),
          longitude=basemap_gdf.geometry.centroid.x.mean(),
          zoom=14,
          pitch=45,
      )

      # レイヤーの作成

      basemap_layer = pdk.Layer(
          "GeoJsonLayer",
          data=basemap_gdf,
          get_fill_color=[255, 255, 255, 200],
          get_line_color=[0, 0, 0],
          get_line_width=2,
          pickable=True,
          extruded=True,
          get_elevation="measuredHeight",
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
          get_elevation="measuredHeight",
      )

      # Deckインスタンスの作成と表示
    #   print(basemap_layer)
    #   print(building_layer)
      deck = pdk.Deck(layers=[basemap_layer,building_layer], initial_view_state=view_state)
      deck.show()
    else :
      pass
    
    # basemap_json = json.loads(basemap_gdf.to_json())
    building_json = json.loads(building_gdf.to_json())
    lines_json = json.dumps(dict(), indent=2, ensure_ascii=False)

    # save_json_to_directory(json_data=basemap_json, filename='basemap.json')
    save_json_to_directory(json_data=building_json, filename='building.json')
    save_json_to_directory(json_data=lines_json, filename='lines.json')

    return building_json


### 道路選択ツール
@tool
def getroad_by_name(road_name, visualize=False):
    '''Retrieve road information by road name'''
    def get_node_coords(node_id):
        node = gdf_nodes[gdf_nodes["osmid"] == node_id].iloc[0]
        return [node.x, node.y, 0]

    G = ox.graph_from_place('Toshima, Tokyo, Japan', network_type='walk')
    sub_edges = []
    sub_nodes = set()

    for u, v, k, data in G.edges(keys=True, data=True):
        if road_name in data.get('name', ''):
            sub_edges.append((u, v, k))
            sub_nodes.add(u)
            sub_nodes.add(v)

    H = G.edge_subgraph(sub_edges)
    gdf_nodes, gdf_edges = ox.graph_to_gdfs(H, nodes=True, edges=True, node_geometry=True, fill_edge_geometry=True)
    gdf_edges = gdf_edges.reset_index()
    gdf_nodes = gdf_nodes.reset_index()

    line_data = []
    for row in gdf_edges.itertuples(index=False):
        edge = row._asdict()
        if isinstance(edge["name"], list):
            break
        line_data.append({
            "from": get_node_coords(edge["u"]),
            "to": get_node_coords(edge["v"]),
            "length": edge["length"],
            "grade": None,
            "oneway": edge["oneway"],
            "highway": edge["highway"],
            "name": edge["name"] if not pd.isna(edge["name"]) else "",
            "maxspeed": None,
            "lanes": None,
        })

    if visualize:
        line_layer = pdk.Layer(
            "LineLayer",
            line_data,
            get_source_position="from",
            get_target_position="to",
            get_color=[255, 0, 0],
            get_width=5,
        )
        view_state = pdk.ViewState(
            longitude=139.7188,
            latitude=35.7295,
            zoom=14,
            pitch=50,
        )
        deck = pdk.Deck(layers=[line_layer], initial_view_state=view_state)
        deck.show()

    building_json = json.dumps(dict(), indent=2, ensure_ascii=False)
    lines_json = json.dumps(line_data, indent=2, ensure_ascii=False)
    # print(lines_json)

    save_json_to_directory(json_data=building_json, filename='building.json')
    save_json_to_directory(json_data=line_data, filename='lines.json')

    return lines_json


### 最短経路探索ツール
@tool
def getroad_from_points(start_point:tuple=(35.7295, 139.7109),end_point:tuple= (35.73089558924716, 139.7186283707542),visualize:bool=False):
    """
    Retrieve the shortest path from one point to another point.

    Parameters
    ----------
    start_point : tuple
        始点の座標 (lat,lon)
    end_point : tuple
        終点の座標 (lat,lon)
    visualize : bool
        可視化の有無

    Returns
    -------
    line_json : str
        LineLayer用のjson

    """

    def get_node_coords(node_id):
        node = gdf_nodes[gdf_nodes["osmid"] == node_id].iloc[0]
        # return [node.x, node.y, int(node.elevation)]
        return [node.x, node.y, 0]  # 高さは0にする

    G = ox.graph_from_place('Toshima, Tokyo, Japan', network_type='walk')


    # 最寄りのノードを取得
    start_node = ox.nearest_nodes(G, start_point[1], start_point[0])
    end_node = ox.nearest_nodes(G, end_point[1], end_point[0])

    # 最短経路を計算
    route = nx.shortest_path(G, start_node, end_node, weight='length')

    # サブグラフを作成
    H = G.subgraph(route)

    gdf_nodes, gdf_edges = ox.graph_to_gdfs(
        H,
        nodes=True, edges=True,
        node_geometry=True,
        fill_edge_geometry=True)

    gdf_edges = gdf_edges.reset_index()
    gdf_nodes = gdf_nodes.reset_index()

    #linelayerを生成


    line_data = []

    for row in gdf_edges.itertuples(index=False):
        edge = row._asdict()

        if isinstance(edge["name"], list):
            break

        name = edge["name"]

        line_data.append(
            {
                "from": get_node_coords(edge["u"]),
                "to": get_node_coords(edge["v"]),
                "length": edge["length"],
                "grade": None,
                "oneway": edge["oneway"],
                "highway": edge["highway"],
                "name": edge["name"] if not pd.isna(edge["name"]) else "",
                "maxspeed": None,
                "lanes": None,
            }
        )

    if visualize:
        # LineLayerを作成
        line_layer = pdk.Layer(
            "LineLayer",
            line_data,
            get_source_position="from",  # 始点の指定
            get_target_position="to",    # 終点の指定
            get_color=[255, 0, 0],        # 線の色（赤）
            get_width=5,                  # 線の太さ
        )

        # 地図の初期設定（池袋サンシャインシティに変更）
        view_state = pdk.ViewState(
            longitude=139.7188,  # サンシャインシティの経度
            latitude=35.7295,    # サンシャインシティの緯度
            zoom=14,             # ズームレベル
            pitch=50,            # 3D表示のためのピッチ角
        )

        # Deckオブジェクトの作成
        deck = pdk.Deck(layers=[line_layer], initial_view_state=view_state)

        # 地図の表示
        deck.show()


    building_json = json.dumps(dict(), indent=2, ensure_ascii=False)
    lines_json = json.dumps(line_data, indent=2, ensure_ascii=False)

    save_json_to_directory(json_data=building_json, filename='building.json')
    save_json_to_directory(json_data=line_data, filename='lines.json')

    return lines_json


### レストラン情報取得ツール
@tool
def getrestaurants(visualize=False):
    '''Retrieve information about Asian restaurants within a 3km radius of Ikebukuro Station.'''

    # APIキーの取得
    load_dotenv()
    API_KEY = os.getenv('HOTPEPPER_API_KEY')

    # hotpepper からレストラン情報を取得
    URL = 'http://webservice.recruit.co.jp/hotpepper/gourmet/v1/'

    #池袋駅から半径3km以内のアジア料理を取得

    body = {
        'key':API_KEY,
        'genre':'G009',
        'lat':35.728926,
        'lng':139.71038,
        'range':5,
        'format':'json',
        'count':100
    }
    #api request
    response = requests.get(URL,body)
    #取得したデータからJSONデータを取得
    datum = response.json()
    #JSONデータの中からお店のデータを取得
    stores = datum['results']['shop']
    #お店のデータの中から、店名を抜き出してgdfに変換
    for store_name in stores:
        name = store_name['name']

    df_stores = pd.DataFrame(stores)
    gdf_stores = gpd.GeoDataFrame(
        df_stores, geometry=gpd.points_from_xy(df_stores.lng, df_stores.lat), crs="EPSG:4326"
    )

    #plateauから建物データを取得
    tokyo23ku = load_dataset("plateau-tokyo23ku-2022.cloud")
    area = tokyo23ku.area_from_landmark(landmark="サンシャインシティ",min_size=[1500,1500])
    base_building_gdf  = area.gdf


    #建物との交差判定
    joined_gdf = gpd.sjoin(gdf_stores, base_building_gdf, how="inner", predicate="within")
    base_building_gdf['store_dummy'] = base_building_gdf['buildingId'].isin(joined_gdf['buildingId']).astype(int)

    #ベースの建物と，レストランが入った建物をそれぞれ切り分け
    basemap_gdf = base_building_gdf
    building_gdf = base_building_gdf.query('store_dummy==1')

    if visualize:

      # ビューの設定
      view_state = pdk.ViewState(
          latitude=basemap_gdf.geometry.centroid.y.mean(),
          longitude=basemap_gdf.geometry.centroid.x.mean(),
          zoom=14,
          pitch=45,
      )

      basemap_layer = pdk.Layer(
          "GeoJsonLayer",
          data=basemap_gdf,
          get_fill_color=[255, 255, 255, 200],
          get_line_color=[0, 0, 0],
          get_line_width=2,
          pickable=True,
          extruded=True,
          get_elevation="measuredHeight",
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
          get_elevation="measuredHeight",
      )

      # Deckインスタンスの作成と表示
      deck = pdk.Deck(layers=[basemap_layer, building_layer], initial_view_state=view_state)
      deck.show()
    else:
      pass

    # basemap_json = json.loads(basemap_gdf.to_json())
    building_json = json.loads(building_gdf.to_json())
    lines_json = json.dumps(dict(), indent=2, ensure_ascii=False)

    # save_json_to_directory(json_data=basemap_json, filename='basemap.json')
    save_json_to_directory(json_data=building_json, filename='building.json')
    save_json_to_directory(json_data=lines_json, filename='lines.json')

    return building_json


### 建物建築ツール
@tool
def buildbuilding(building_type='大きい',visualize=False):
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

    """
    tokyo23ku = load_dataset("plateau-tokyo23ku-2022.cloud")
    area = tokyo23ku.area_from_landmark('サンシャインシティ',min_size=[1500,1500])
    basemap_gdf = area.gdf
    """


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
      """

      basemap_layer = pdk.Layer(
          "GeoJsonLayer",
          data=basemap_gdf,
          get_fill_color=[255, 255, 255, 200],
          get_line_color=[0, 0, 0],
          get_line_width=2,
          pickable=True,
          extruded=True,
          get_elevation="measuredHeight",
      )
      """

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
      # deck = pdk.Deck(layers=[basemap_layer,building_layer], initial_view_state=view_state)
      deck = pdk.Deck(layers=[building_layer], initial_view_state=view_state)
      deck.show()
    else :
      pass

    """

    basemap_json = json.loads(basemap_gdf.to_json())
    """
    building_json = json.loads(building_gdf.to_json())
    lines_json = json.dumps(dict(), indent=2, ensure_ascii=False)

    save_json_to_directory(json_data=building_json, filename='building.json')
    save_json_to_directory(json_data=lines_json, filename='lines.json')

    return building_json