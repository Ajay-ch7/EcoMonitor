import { useEffect, useState } from "react";

import MapView, { type BBox } from "./MapView";

interface Region {
  name: string;
  bbox: BBox;
}

// The region comes from config/settings.yaml via GET /region.
export default function App() {
  const [region, setRegion] = useState<Region | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/region")
      .then((res) => (res.ok ? res.json() : Promise.reject(new Error(`HTTP ${res.status}`))))
      .then(setRegion)
      .catch((e: Error) => setError(`API unreachable (${e.message})`));
  }, []);

  return (
    <>
      <div className="badge">
        Land Emissions Monitor
        {region && ` · ${region.name}`}
        {error && ` · ${error}`}
      </div>
      {region && <MapView bbox={region.bbox} />}
    </>
  );
}
