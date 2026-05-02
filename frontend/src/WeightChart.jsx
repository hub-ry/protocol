import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

export default function WeightChart({ data }) {
  if (!data.length) return <p>Loading...</p>;

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="date" tick={{ fontSize: 12 }} />
        {/* domain="auto" lets Recharts zoom the Y axis to your actual weight range */}
        <YAxis domain={["auto", "auto"]} tick={{ fontSize: 12 }} />
        <Tooltip />
        <Line type="monotone" dataKey="weight" dot={true} strokeWidth={2} />
      </LineChart>
    </ResponsiveContainer>
  );
}
