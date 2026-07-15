"use client";

import { FormEvent, useEffect, useState } from "react";
import { api } from "@/lib/api";

type Professor = { id: number; full_name: string; scopus_author_id?: string; is_active: boolean; profile_status: string };

export default function Manage() {
  const [items, setItems] = useState<Professor[]>([]);
  const [message, setMessage] = useState("");
  const [removing, setRemoving] = useState<Professor>();
  const [password, setPassword] = useState("");
  const [removeBusy, setRemoveBusy] = useState(false);
  const load = () => api<Professor[]>("/professors?include_inactive=true").then(setItems);
  useEffect(() => { load(); }, []);

  async function add(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const entries = Array.from(new FormData(form).entries()).filter(([, value]) => typeof value !== "string" || value.trim() !== "");
    try {
      await api("/professors", { method: "POST", body: JSON.stringify(Object.fromEntries(entries)) });
      form.reset(); setMessage("Professor added. Confirm their Scopus profile, then update from Scopus."); load();
    } catch (error) { setMessage(error instanceof Error ? error.message : "Unable to add professor"); }
  }

  async function sync(id: number) {
    setMessage("Updating from Scopus...");
    try {
      const result = await api<{ created: number; updated: number }>(`/professors/${id}/sync`, { method: "POST" });
      setMessage(`Update complete: ${result.created} new and ${result.updated} changed publications.`); load();
    } catch (error) { setMessage(error instanceof Error ? error.message : "Update failed"); }
  }

  async function removeProfessor(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!removing) return;
    setRemoveBusy(true);
    try {
      const result = await api<{ removed_name: string }>(`/professors/${removing.id}`, { method: "DELETE", body: JSON.stringify({ password }) });
      setMessage(`${result.removed_name} and their unshared publication data were removed.`);
      setRemoving(undefined); setPassword(""); await load();
    } catch (error) { setMessage(error instanceof Error ? error.message : "Unable to remove professor"); }
    finally { setRemoveBusy(false); }
  }

  return <>
    <h1 className="text-3xl font-bold">Manage professors</h1>
    <p className="text-slate-500 mt-2">Add researchers, connect their confirmed Scopus profile and update publication data.</p>
    {message && <p className="card p-3 mt-5">{message}</p>}
    <form onSubmit={add} className="card p-5 mt-5 grid md:grid-cols-2 xl:grid-cols-4 gap-4">
      <label className="label">Full name<input className="input mt-1" name="full_name" required /></label>
      <label className="label">Academic title<input className="input mt-1" name="academic_title" /></label>
      <label className="label">Research area (optional)<input className="input mt-1" name="research_area" /></label>
      <label className="label">Email (optional)<input className="input mt-1" name="email" type="email" /></label>
      <label className="label">ORCID<input className="input mt-1" name="orcid" /></label>
      <label className="label">Scopus Author ID<input className="input mt-1" name="scopus_author_id" /></label>
      <label className="label md:col-span-2">Institution<input className="input mt-1" name="institution_name" defaultValue="University of Technology Nuremberg" /></label>
      <button className="btn w-fit">Add professor</button>
    </form>
    <div className="card mt-5 overflow-auto"><table className="table"><thead><tr><th>Professor</th><th>Scopus profile</th><th>Status</th><th>Actions</th></tr></thead><tbody>{items.map((professor) => <tr key={professor.id}><td className="font-bold">{professor.full_name}</td><td>{professor.scopus_author_id || "Not connected"}</td><td><span className="badge">{professor.is_active ? "Active" : "Inactive"}</span></td><td className="flex flex-wrap gap-2"><button type="button" className="btn text-sm" disabled={!professor.scopus_author_id} onClick={() => sync(professor.id)}>Update from Scopus</button><button type="button" className="btn btn-secondary text-sm" onClick={async () => { await api(`/professors/${professor.id}/${professor.is_active ? "deactivate" : "activate"}`, { method: "POST" }); load(); }}>{professor.is_active ? "Deactivate" : "Activate"}</button><button type="button" className="btn text-sm bg-red-700 hover:bg-red-800" onClick={() => { setRemoving(professor); setPassword(""); }}>Remove</button></td></tr>)}</tbody></table></div>

    {removing && <div className="fixed inset-0 z-50 bg-slate-950/50 grid place-items-center p-4" role="dialog" aria-modal="true" aria-labelledby="remove-professor-title"><form onSubmit={removeProfessor} className="card p-6 w-full max-w-md"><p className="text-sm font-bold text-red-700">PERMANENT REMOVAL</p><h2 id="remove-professor-title" className="text-2xl font-bold mt-1">Remove {removing.full_name}?</h2><p className="text-sm text-slate-600 mt-3">This removes the professor, their collaboration links, synchronization history, and publications not shared with another professor. Enter your current administrator password to confirm.</p><label className="label block mt-5">Admin password<input className="input mt-1" type="password" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="current-password" required autoFocus /></label><div className="flex justify-end gap-3 mt-6"><button type="button" className="btn btn-secondary" onClick={() => { setRemoving(undefined); setPassword(""); }} disabled={removeBusy}>Cancel</button><button className="btn bg-red-700 hover:bg-red-800" disabled={removeBusy}>{removeBusy ? "Removing..." : "Remove permanently"}</button></div></form></div>}
  </>;
}
