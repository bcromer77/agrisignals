"use client";
import { useEffect, useState } from "react";
import AlertsTicker from "@/components/alerts-ticker";

interface Composite {
  state: string;
  labor_risk: number;
  water_risk: number;
  composite_score: number;
}

export default function DashboardPage() {
  const apiBase = process.env.NEXT_PUBLIC_API_BASE!;
  const [summary, setSummary] = useState<any>(null);
  const [composites, setComposites] = useState<Composite[]>([]);

  useEffect(() => {
    fetch(`${apiBase}/stats/summary`)
      .then((res) => res.json())
      .then(setSummary)
      .catch(console.error);

    fetch(`${apiBase}/stats/composite`)
      .then((res) => res.json())
      .then(setComposites)
      .catch(console.error);
  }, [apiBase]);

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold">🌱 AgriSignals Dashboard</h1>

      <AlertsTicker />

      <section>
        <h2 className="mt-4 font-semibold">Summary</h2>
        <pre className="bg-gray-100 p-2 rounded text-xs overflow-x-scroll">
          {JSON.stringify(summary, null, 2)}
        </pre>
      </section>

      <section>
        <h2 className="mt-4 font-semibold">Composite Scores</h2>
        <table className="min-w-full text-sm border">
          <thead className="bg-gray-200">
            <tr>
              <th className="p-2 border">State</th>
              <th className="p-2 border">Labor Risk</th>
              <th className="p-2 border">Water Risk</th>
              <th className="p-2 border">Composite</th>
            </tr>
          </thead>
          <tbody>
            {composites.map((c) => (
              <tr key={c.state}>
                <td className="p-2 border">{c.state}</td>
                <td className="p-2 border">{c.labor_risk.toFixed(2)}</td>
                <td className="p-2 border">{c.water_risk.toFixed(2)}</td>
                <td className="p-2 border font-bold">{c.composite_score.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
