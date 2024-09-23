import {
  AmbientLight,
  DirectionalLight,
  LightingEffect,
  PointLight,
} from "@deck.gl/core";
import { DataFilterExtension, _TerrainExtension as TerrainExtension } from '@deck.gl/extensions';
import { Tile3DLayer } from "@deck.gl/geo-layers";
import { GeoJsonLayer } from "@deck.gl/layers";
import DeckGL from "@deck.gl/react";
import * as d3 from "d3";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import React, { useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { Map } from "react-map-gl";

export const lightingEffect = new LightingEffect({
  ambientLight: new AmbientLight({
    color: [255, 182, 193],
    intensity: 0.6,
  }),
  pointLight1: new PointLight({
    color: [255, 255, 255],
    intensity: 0.8,
    position: [-0.144528, 49.739968, 80000],
  }),
  pointLight2: new PointLight({
    color: [255, 255, 255],
    intensity: 0.8,
    position: [-3.807751, 54.104682, 8000],
  }),
  directionalLight: new DirectionalLight({
    color: [255, 255, 255],
    intensity: 0.8,
    direction: [-3, -9, -1],
  }),
});

export const MATERIAL = {
  ambient: 0.8,
  diffuse: 0.6,
  shininess: 300,
  specularColor: [255, 255, 255],
};

const BUILDING_HIGHT_OFFSET = -80;
const creditsElement = document.getElementById('credits');

const INITIAL_VIEW_STATE = {
  longitude: 139.536321,
  latitude: 35.644555,
  zoom: 16,
  pitch: 50,
  bearing: 0,
};

function getTooltip({ object }) {
  if (!object) {
    return null;
  }
  const str_lines = [
    `name: ${object.name}`,
    `grade: ${object.grade}`,
    `length: ${object.length}`,
    `oneway: ${object.oneway}`,
    `highway: ${object.highway}`,
    `maxspeed: ${object.maxspeed}`,
    `lanes: ${object.lanes}`,
  ];
  return str_lines.join("\n");
}

const gradeColorScale = d3
  .scaleSequential()
  .domain([-0.5, 0.5])
  .interpolator(d3.interpolateRdBu);

const lengthColorScale = d3
  .scaleSequential()
  .domain([0, 200])
  .interpolator(d3.interpolateBlues);

const ordinalColorScale = d3.scaleOrdinal(d3.schemeCategory10);

export default function App({
  initialLineWidth = 3,
  initialColorMode = "length",
  lines = "./lines.json",
  baseGeoJsonData = "./basemap.json",      // ベースマップ
  siteGeoJsonData = './site.json',         // 対象敷地
  floodingGeoJsonData = "./flooding.json", // 浸水想定範囲
  sheltersGeoJsonData = "./shelters.json", // 避難所
  
  mapStyle = "https://basemaps.cartocdn.com/gl/dark-matter-nolabels-gl-style/style.json",
  initialBuildingOpacity = 0.8,
}) {
  const [lineWidth, setLineWidth] = useState(initialLineWidth);

  const [colorMode, setColorMode] = useState(initialColorMode);

  const [buildingOpacity, setBuildingOpacity] = useState(
    initialBuildingOpacity,
  );

  const getColor = useMemo(() => {
    return (d) => {
      if (colorMode === "grade") {
        const colorObj = d3.color(gradeColorScale(d.grade));
        const color = [colorObj.r, colorObj.g, colorObj.b, 255];
        return color;
      }

      if (colorMode === "length") {
        const colorObj = d3.color(lengthColorScale(d.length));
        const color = [colorObj.r, colorObj.g, colorObj.b, 255];
        return color;
      }

      if (colorMode === "oneway") {
        return d.oneway ? [253, 128, 93] : [23, 184, 190];
      }

      if (colorMode === "highway") {
        const colorObj = d3.color(ordinalColorScale(d.highway));
        return [colorObj.r, colorObj.g, colorObj.b, 255];
      }

      if (colorMode === "maxspeed") {
        if (!d.maxspeed) return [255, 255, 255, 32];
        const colorObj = d3.color(ordinalColorScale(d.maxspeed));
        return [colorObj.r, colorObj.g, colorObj.b, 255];
      }

      if (colorMode === "lanes") {
        if (!d.lanes) return [255, 255, 255, 32];
        const colorObj = d3.color(ordinalColorScale(d.lanes));
        return [colorObj.r, colorObj.g, colorObj.b, 255];
      }

      return [0, 255, 0];
    };
  }, [colorMode]);

  const [credits, setCredits] = useState('');

  const layers = [
    new Tile3DLayer({
        id: 'google-3d-tiles',
        data: 'https://tile.googleapis.com/v1/3dtiles/root.json',
        onTilesetLoad: tileset3d => {
            tileset3d.options.onTraversalComplete = selectedTiles => {
                const uniqueCredits = new Set();
                selectedTiles.forEach(tile => {
                    const { copyright } = tile.content.gltf.asset;
                    copyright.split(';').forEach(uniqueCredits.add, uniqueCredits);
                    setCredits([...uniqueCredits].join('; '));
                });
                return selectedTiles;
            }
        },
        loadOptions: {
            fetch: {
                headers: {
                    'X-GOOG-API-KEY':
                }
            }
        },
        operation: 'terrain+draw'
    }),
    baseGeoJsonData && new GeoJsonLayer({
      id: 'basegeojson-layer',
      data: baseGeoJsonData, // 読み込まれたGeoJSONデータを渡す
      extensions: [new DataFilterExtension({filterSize: 1}), new TerrainExtension()],
      pickable: true,
      stroked: false,
      filled: true,
      extruded: true,
      getFillColor: [255, 255, 255, 100],  // [255, 255, 0, 200],
      getLineWidth: 2,
      getElevation: (f) => f.properties.measuredHeight || 0, // 高さを設定
      getLineColor: [0, 0, 0, 255], // 辺の色
    }),
    siteGeoJsonData && new GeoJsonLayer({
      id: 'sitegeojson-layer',
      data: siteGeoJsonData, // 読み込まれたGeoJSONデータを渡す
      pickable: true,
      stroked: false,
      filled: true,
      extruded: true,
      getFillColor: [255, 0, 0, 200],  // [255, 255, 0, 200],
      getLineWidth: 2,
      getElevation: (f) => f.properties.setHeight || 0, // 高さを設定
      getLineColor: [0, 0, 0, 255], // 辺の色
    }),
    floodingGeoJsonData && new GeoJsonLayer({
      id: 'floodinggeojson-layer',
      data: floodingGeoJsonData, // 読み込まれたGeoJSONデータを渡す
      // pickable: true,
      stroked: false,
      filled: true,
      extruded: true,
      getFillColor: [0, 170, 255, 150],
      getElevation: (f) => f.properties.measuredHeight || 0, // 高さを設定
      extensions: [new TerrainExtension()],
    }),
    sheltersGeoJsonData && new GeoJsonLayer({
      id: "icon",
      data: "./shelters.json",
      stroked: true,
      filled: true,
      pointType: "icon",
      //iconの設定
      getIcon: () => { return {
        url: "./images/marker.png",
        x: 0, //画像読み込みのX軸オフセット
        y: 0, //画像読み込みのY軸オフセット
        z: 200, //画像読み込みのZ軸オフセット
        anchorY: 512, //Y軸の表示位置（通常画像の縦幅に合わせる）
        width: 512, //アイコン画像の横幅
        height: 512, //アイコン画像の縦幅
        mask: true //tureにするとアイコン画像の色の上塗りなどが可能になる
      }},
      getElevation: (f) => 200, // 高さを設定
      extensions: [new TerrainExtension()],
      iconSizeScale: 60,
      getIconColor: [255, 124, 0] //オレンジ色
    }),
  ];

  return (
    <>
      <div className="absolute left-5 top-5 z-10 bg-neutral-900/80 text-white p-3 flex flex-col gap-2">
        <h1 className="font-bold text-lg">Geo Discussion Facilitator AI</h1>
      </div>

      <DeckGL
        style={{ width: '66%', height: '100%'}} // DeckGLのスタイルを設定
        layers={layers}
        initialViewState={INITIAL_VIEW_STATE}
        controller={true}
        pickingRadius={5}
        // parameters={{
        //   blendFunc: [GL.SRC_ALPHA, GL.ONE, GL.ONE_MINUS_DST_ALPHA, GL.ONE],
        //   blendEquation: GL.FUNC_ADD,
        //   antialias: true,
        // }}
        effects={[lightingEffect]} // lightingEffect を effects プロパティに設定
      >
        <Map
          reuseMaps
          mapLib={maplibregl}
          mapStyle={mapStyle}
          preventStyleDiffing={true}
          style={{ width: '66%', height: '100%' }} // Mapのスタイルを設定
        />
      </DeckGL>
    </>
  );
}

export function renderToDOM(container) {
  createRoot(container).render(<App />);
}
