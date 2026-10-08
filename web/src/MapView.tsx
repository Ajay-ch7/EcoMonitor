import maplibregl, { type StyleSpecification } from "maplibre-gl";
import { useEffect, useRef } from "react";

export type BBox = [number, number, number, number];

const OSM_STYLE: StyleSpecification = {
  version: 8,
  sources: {
    osm: {
      type: "raster",
      tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
      tileSize: 256,
      maxzoom: 19,
      attribution: "© OpenStreetMap contributors",
    },
  },
  layers: [{ id: "osm", type: "raster", source: "osm" }],
};

export default function MapView({ bbox }: { bbox: BBox }) {
  const container = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!container.current) return;
    const map = new maplibregl.Map({
      container: container.current,
      style: OSM_STYLE,
      bounds: [
        [bbox[0], bbox[1]],
        [bbox[2], bbox[3]],
      ],
      fitBoundsOptions: { padding: 40 },
    });
    map.addControl(new maplibregl.NavigationControl(), "top-right");
    map.addControl(new maplibregl.ScaleControl(), "bottom-left");
    return () => map.remove();
  }, [bbox]);

  return <div ref={container} className="map" />;
}
