import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

// Convert "2025-08-26" → "Aug 26"
// We split manually instead of passing to `new Date(str)` directly because
// parsing "YYYY-MM-DD" as a Date assumes UTC midnight, which shifts the day
// backward by one in timezones behind UTC.
function formatDate(dateStr) {
  const [year, month, day] = dateStr.split("-").map(Number);
  return new Date(year, month - 1, day).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });
}

// Custom tooltip rendered when hovering a data point
function WeightTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div
      style={{
        background: "#fff",
        border: "1px solid #e5e7eb",
        borderRadius: 6,
        padding: "8px 12px",
        fontSize: 13,
      }}
    >
      <p style={{ margin: 0, color: "#6b7280" }}>{formatDate(label)}</p>
      <p style={{ margin: "4px 0 0", fontWeight: 600 }}>
        {payload[0].value} lbs
      </p>
    </div>
  );
}

export default function WeightChart({ data }) {
  if (!data.length) return <p>Loading...</p>;

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis
          dataKey="date"
          tickFormatter={formatDate}
          tick={{ fontSize: 11, fill: "#6b7280" }}
          // preserveStartEnd always shows the first and last date, then fills
          // in evenly-spaced ticks between them so the axis isn't crowded.
          interval="preserveStartEnd"
        />
        <YAxis
          domain={["auto", "auto"]}
          tick={{ fontSize: 11, fill: "#6b7280" }}
          unit=" lbs"
        />
        <Tooltip content={<WeightTooltip />} />
        <Line
          type="monotone"
          dataKey="weight"
          stroke="#3b82f6"
          strokeWidth={2}
          dot={{ r: 3, fill: "#3b82f6" }}
          activeDot={{ r: 5 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
