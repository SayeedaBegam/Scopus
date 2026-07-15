"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

type Datum = { name: string; value: number };

export function RankedChart({ data, color = "#006d77", limit = 12 }: { data: Datum[]; color?: string; limit?: number }) {
  return <ResponsiveContainer width="100%" height={320}><BarChart data={data.slice(0, limit)} layout="vertical" margin={{ left: 20, right: 20 }}><CartesianGrid strokeDasharray="3 3" /><XAxis type="number" allowDecimals={false} /><YAxis type="category" dataKey="name" width={130} tick={{ fontSize: 12 }} /><Tooltip /><Bar dataKey="value" fill={color} radius={[0, 5, 5, 0]} /></BarChart></ResponsiveContainer>;
}

const colors = ["#006d77", "#f4b942", "#4c78a8", "#72b7b2", "#e45756", "#54a24b", "#b279a2", "#9d755d"];

export function CountryDonut({ data }: { data: Datum[] }) {
  const visible = data.slice(0, 7);
  const other = data.slice(7).reduce((total, item) => total + item.value, 0);
  const chartData = other ? [...visible, { name: "Other", value: other }] : visible;
  return <ResponsiveContainer width="100%" height={320}><PieChart><Pie data={chartData} dataKey="value" nameKey="name" innerRadius={70} outerRadius={115} paddingAngle={2}>{chartData.map((item, index) => <Cell key={item.name} fill={colors[index % colors.length]} />)}</Pie><Tooltip /></PieChart></ResponsiveContainer>;
}

export function TrendChart({ data }: { data: Datum[] }) {
  const ordered = [...data].sort((a, b) => Number(a.name) - Number(b.name));
  return <ResponsiveContainer width="100%" height={320}><LineChart data={ordered} margin={{ left: 0, right: 20, top: 15, bottom: 5 }}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="name" /><YAxis allowDecimals={false} /><Tooltip /><Line type="monotone" dataKey="value" stroke="#006d77" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 6 }} /></LineChart></ResponsiveContainer>;
}
