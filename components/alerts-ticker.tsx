"use client";
import { useEffect, useState } from "react";

export default function AlertsTicker() {
  const [alerts, setAlerts] = useState<string[]>([]);

  useEffect(() => {
    const apiBase = process.env.NEXT_PUBLIC_API_BASE!;
    const eventSource = new EventSource(`${apiBase}/sse/alerts`);

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setAlerts((prev) => [data.message, ...prev].slice(0, 5)); // keep last 5
      } catch {
        console.error("Invalid SSE message:", event.data);
      }
    };

    eventSource.onerror = () => {
      console.error("SSE connection error");
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  }, []);

  return (
    <div className="bg-yellow-100 border border-yellow-400 text-yellow-800 p-2 rounded">
      <h2 className="font-bold text-sm">⚡ Live Alerts</h2>
      <ul className="text-xs space-y-1 mt-1">
        {alerts.length === 0 && <li>No alerts yet...</li>}
        {alerts.map((msg, i) => (
          <li key={i}>• {msg}</li>
        ))}
      </ul>
    </div>
  );
}
