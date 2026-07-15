"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import Metrics from "@/components/Metrics";
import { CountryDonut, RankedChart, TrendChart } from "@/components/Charts";
import { api } from "@/lib/api";

type Datum = { name: string; value: number };
type ProfessorRow = { id: number; name: string; international_publications: number; partner_institutions: number; partner_countries: number; collaboration_records: number };
type AnalyticsData = { summary: Record<string, number>; by_country: Datum[]; by_institution: Datum[]; by_year: Datum[]; professor_directory: ProfessorRow[] };

export default function Analytics() {
  const [analytics, setAnalytics] = useState<AnalyticsData>();
  const [query, setQuery] = useState("");
  const [visible, setVisible] = useState(25);
  useEffect(() => { api<AnalyticsData>("/analytics/overall").then(setAnalytics); }, []);
  const professors = useMemo(() => (analytics?.professor_directory || []).filter((item) => item.name.toLowerCase().includes(query.toLowerCase())), [analytics, query]);
  if (!analytics) return <p>Loading analytics…</p>;

  return <>
    <p className="text-sm font-bold text-utn-teal">ORGANISATION OVERVIEW</p>
    <h1 className="text-3xl font-bold mt-1 mb-6">International research partnerships</h1>
    <Metrics items={[{ label: "Professors monitored", value: analytics.summary.professors_monitored }, { label: "International publications", value: analytics.summary.international_publications }, { label: "Partner institutions", value: analytics.summary.partner_institutions }, { label: "Needs review", value: analytics.summary.needs_review }]} />
    <div className="grid xl:grid-cols-2 gap-5 mt-5">
      <section className="card p-5"><h2 className="font-bold text-lg">Country distribution</h2><p className="text-sm text-slate-500">Top countries are shown individually; the remainder are grouped.</p><CountryDonut data={analytics.by_country} /><div className="flex flex-wrap gap-2">{analytics.by_country.slice(0, 8).map((item) => <span className="badge" key={item.name}>{item.name}: {item.value}</span>)}</div></section>
      <section className="card p-5"><h2 className="font-bold text-lg">International publications over time</h2><p className="text-sm text-slate-500">Trend by publication year.</p><TrendChart data={analytics.by_year} /></section>
      <section className="card p-5 xl:col-span-2"><h2 className="font-bold text-lg">Leading partner institutions</h2><p className="text-sm text-slate-500">Top 15 by collaboration records.</p><RankedChart data={analytics.by_institution} limit={15} /></section>
    </div>
    <section className="card p-5 mt-5">
      <div className="flex flex-wrap justify-between items-end gap-4"><div><h2 className="font-bold text-lg">Professor directory</h2><p className="text-sm text-slate-500">Searchable and designed to scale beyond a short chart.</p></div><label className="label">Search professors<input className="input mt-1 w-72" value={query} onChange={(event) => { setQuery(event.target.value); setVisible(25); }} placeholder="Name" /></label></div>
      <div className="overflow-auto mt-4"><table className="table"><thead><tr><th>Professor</th><th>International publications</th><th>Partner institutions</th><th>Partner countries</th><th>Collaboration records</th></tr></thead><tbody>{professors.slice(0, visible).map((item) => <tr key={item.id}><td><Link className="font-bold text-utn-teal hover:underline" href={`/professors/${item.id}`}>{item.name}</Link></td><td>{item.international_publications}</td><td>{item.partner_institutions}</td><td>{item.partner_countries}</td><td>{item.collaboration_records}</td></tr>)}</tbody></table></div>
      {visible < professors.length && <button className="btn btn-secondary mt-4" onClick={() => setVisible((count) => count + 25)}>Show 25 more</button>}
      {!professors.length && <p className="text-center text-slate-500 py-8">No professors match this search.</p>}
    </section>
  </>;
}
