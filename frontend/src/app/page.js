import MapPanel from "../components/MapPanel";
import AlertsPanel from "../components/AlertsPanel";
import VehiclesTable from "../components/VehiclesTable";
import StatsPanel from "../components/StatsPanel";
import Link from "next/link";

export default function Home() {
  return (
    <div>
      <header className="mb-4 animate-fade-in">
        <h1 className="text-2xl font-bold" style={{ color: 'var(--primary)' }}>AI-Powered ALPR & Smart Police Monitoring</h1>
        <div className="flex items-center justify-between">
          <p className="text-sm text-gray-600">Live simulation: license plate reading, alerts, tracking, and predictions</p>
          <nav className="text-sm">
            <Link href="/dataset" className="underline underline-offset-2">Open Dataset Viewer</Link>
          </nav>
        </div>
      </header>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <MapPanel />
        <AlertsPanel />
        <VehiclesTable />
        <StatsPanel />
      </div>
    </div>
  );
}
