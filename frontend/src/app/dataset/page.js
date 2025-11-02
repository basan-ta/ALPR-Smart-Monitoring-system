import DatasetViewer from "../../components/DatasetViewer";

export default function DatasetPage() {
  return (
    <div>
      <header className="mb-4 animate-fade-in">
        <h1 className="text-2xl font-bold" style={{ color: 'var(--primary)' }}>Dataset Viewer</h1>
        <p className="text-sm text-gray-600">Real-time loading, validation, sorting, and filtering</p>
      </header>
      <DatasetViewer />
    </div>
  );
}