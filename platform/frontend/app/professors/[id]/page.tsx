"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import { RankedChart } from "@/components/Charts";
import { api, date } from "@/lib/api";

type Professor = { id: number; full_name: string; academic_title?: string; email?: string; orcid?: string; scopus_author_id?: string; research_area?: string; last_successful_sync_at?: string };
type RankedValue = { name: string; value: number };
type Analytics = { summary: Record<string, number>; by_country: RankedValue[]; by_year: RankedValue[]; by_institution: RankedValue[] };
type Publication = { id: number; year?: number; title: string; source_title?: string; doi?: string; scopus_eid: string; citation_count: number };
type Collaboration = { id: number; publication_id: number; year?: number; author_count: number; source_title?: string; publication_title: string; doi?: string; citation_count: number; international_coauthor?: string; institution_name: string; partner_department?: string; country: string };
type PartnerGroup = { institution: string; country: string; researchers: Set<string>; departments: Set<string>; publications: Set<number> };

export default function Profile() {
  const { id } = useParams();
  const [professor, setProfessor] = useState<Professor>();
  const [analytics, setAnalytics] = useState<Analytics>();
  const [publications, setPublications] = useState<Publication[]>([]);
  const [collaborations, setCollaborations] = useState<Collaboration[]>([]);
  const [showPartners, setShowPartners] = useState(true);
  const [partnerQuery, setPartnerQuery] = useState("");

  useEffect(() => {
    Promise.all([
      api<Professor>(`/professors/${id}`),
      api<Analytics>(`/analytics/professors/${id}`),
      api<Publication[]>(`/professors/${id}/publications`),
      api<Collaboration[]>(`/collaborations?professor_id=${id}`),
    ]).then(([professorResult, analyticsResult, publicationResult, collaborationResult]) => {
      setProfessor(professorResult); setAnalytics(analyticsResult); setPublications(publicationResult); setCollaborations(collaborationResult);
    });
  }, [id]);

  const sortedCollaborations = useMemo(() => [...collaborations].sort((a, b) => (b.year || 0) - (a.year || 0) || a.publication_title.localeCompare(b.publication_title)), [collaborations]);
  const partnerGroups = useMemo(() => {
    const groups = new Map<string, PartnerGroup>();
    collaborations.forEach((item) => {
      const key = `${item.institution_name}|${item.country}`;
      const group = groups.get(key) || { institution: item.institution_name, country: item.country, researchers: new Set<string>(), departments: new Set<string>(), publications: new Set<number>() };
      item.international_coauthor?.split(";").map((value) => value.trim()).filter(Boolean).forEach((value) => group.researchers.add(value));
      item.partner_department?.split(";").map((value) => value.trim()).filter(Boolean).forEach((value) => group.departments.add(value));
      group.publications.add(item.publication_id); groups.set(key, group);
    });
    const query = partnerQuery.toLowerCase();
    return [...groups.values()].filter((group) => [group.institution, group.country, ...group.researchers, ...group.departments].some((value) => value.toLowerCase().includes(query))).sort((a, b) => b.publications.size - a.publications.size || a.institution.localeCompare(b.institution));
  }, [collaborations, partnerQuery]);

  if (!professor || !analytics) return <p>Loading professor profile...</p>;
  const profileDetails = [professor.research_area, professor.email].filter(Boolean).join(" | ");
  const metrics = [
    { label: "All Scopus publications", value: analytics.summary.total_publications, description: "Every publication returned for this author" },
    { label: "International publications", value: analytics.summary.international_publications, description: "Publications with at least one non-German partner" },
    { label: "Partner institutions", value: analytics.summary.partner_institutions, description: "Click to show or hide partner details", clickable: true },
    { label: "Partner countries", value: analytics.summary.partner_countries, description: "Countries represented by international partners" },
  ];

  return <>
    <div className="card p-6 flex flex-wrap justify-between gap-4"><div>{professor.academic_title && <p className="text-sm text-utn-teal font-bold">{professor.academic_title}</p>}<h1 className="text-3xl font-bold">{professor.full_name}</h1>{profileDetails && <p className="text-slate-500 mt-1">{profileDetails}</p>}<p className="text-sm mt-3">Scopus Author ID: <b>{professor.scopus_author_id || "Not connected"}</b> | Last updated {date(professor.last_successful_sync_at)}</p></div><button className="btn-secondary btn" onClick={() => fetch(`/api/v1/exports/professor/${id}`, { method: "POST", credentials: "include" })}>Export professor data</button></div>

    <div className="grid sm:grid-cols-2 xl:grid-cols-4 gap-4 mt-5">{metrics.map((metric) => { const content = <><p className="text-sm text-slate-500">{metric.label}</p><p className="text-3xl font-bold mt-1 text-utn-navy">{metric.value}</p><p className="text-xs text-slate-500 mt-2">{metric.description}</p></>; return metric.clickable ? <button key={metric.label} className="card p-5 text-left hover:ring-2 hover:ring-utn-teal transition" onClick={() => setShowPartners((value) => !value)} aria-expanded={showPartners}>{content}</button> : <div className="card p-5" key={metric.label}>{content}</div>; })}</div>

    {showPartners && <section className="card p-5 mt-5"><div className="flex flex-wrap justify-between items-end gap-4"><div><h2 className="font-bold text-lg">International partner directory</h2><p className="text-sm text-slate-500 mt-1">Researchers are grouped with their institution, department or lab, country, and linked publications.</p></div><label className="label">Search partners<input className="input mt-1 w-72" value={partnerQuery} onChange={(event) => setPartnerQuery(event.target.value)} placeholder="Researcher, institution, lab, country" /></label></div><div className="grid lg:grid-cols-2 2xl:grid-cols-3 gap-4 mt-5">{partnerGroups.map((group) => <div className="rounded-xl border border-slate-200 p-4" key={`${group.institution}-${group.country}`}><div className="flex justify-between gap-3 items-start"><h3 className="font-bold text-utn-navy">{group.institution}</h3><span className="badge whitespace-nowrap">{group.country}</span></div><dl className="text-sm mt-4 space-y-3"><div><dt className="text-xs uppercase tracking-wide text-slate-500">Researcher(s)</dt><dd className="font-medium mt-1">{[...group.researchers].join(", ") || "Not provided by Scopus"}</dd></div><div><dt className="text-xs uppercase tracking-wide text-slate-500">Department / lab</dt><dd className="font-medium mt-1">{[...group.departments].join(", ") || "Not provided by Scopus"}</dd></div></dl><p className="text-xs text-slate-500 mt-4">{group.publications.size} linked international publication{group.publications.size === 1 ? "" : "s"}</p></div>)}</div>{!partnerGroups.length && <p className="text-center text-slate-500 py-8">No partner records match this search.</p>}</section>}

    <div className="grid xl:grid-cols-2 gap-5 mt-5"><section className="card p-5"><h2 className="font-bold text-lg mb-3">Collaborations by country</h2><RankedChart data={analytics.by_country} /></section><section className="card p-5"><h2 className="font-bold text-lg mb-3">Collaborations by year</h2><RankedChart data={analytics.by_year} color="#f4b942" /></section></div>

    <section className="card p-5 mt-5 overflow-auto" id="international-publications"><h2 className="font-bold text-lg">International publication details</h2><p className="text-sm text-slate-500 mt-1 mb-4">One row is shown for each publication and international partner institution.</p><table className="table"><thead><tr><th>Year</th><th>No. of author(s)</th><th>Source title</th><th>Publication title</th><th>DOI</th><th>Citations</th><th>Other university researcher(s)</th><th>Other university/institution</th><th>Other university department/lab</th><th>Country</th></tr></thead><tbody>{sortedCollaborations.map((item) => <tr key={item.id}><td>{item.year || "-"}</td><td>{item.author_count}</td><td>{item.source_title || "-"}</td><td className="font-medium">{item.publication_title}</td><td>{item.doi || "-"}</td><td>{item.citation_count}</td><td>{item.international_coauthor || "-"}</td><td>{item.institution_name}</td><td>{item.partner_department || "-"}</td><td>{item.country}</td></tr>)}</tbody></table>{!sortedCollaborations.length && <p className="text-slate-500 py-6 text-center">No international publication records found.</p>}</section>

    <section className="card p-5 mt-5 overflow-auto"><h2 className="font-bold text-lg">All Scopus publications</h2><p className="text-sm text-slate-500 mt-1 mb-4">This includes publications both with and without an identified international partner.</p><table className="table"><thead><tr><th>Year</th><th>Publication</th><th>Source</th><th>DOI</th><th>Scopus EID</th><th>Citations</th></tr></thead><tbody>{publications.map((publication) => <tr key={publication.id}><td>{publication.year || "-"}</td><td className="font-medium">{publication.title}</td><td>{publication.source_title || "-"}</td><td>{publication.doi || "-"}</td><td>{publication.scopus_eid}</td><td>{publication.citation_count}</td></tr>)}</tbody></table></section>
  </>;
}
