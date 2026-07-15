"use client";
import {FormEvent,useEffect,useState} from "react";
import {api,User} from "@/lib/api";

export default function Accounts(){
  const [users,setUsers]=useState<User[]>([]),[message,setMessage]=useState(""),[error,setError]=useState(""),[busy,setBusy]=useState(false);
  const load=()=>api<User[]>("/admin/users").then(setUsers).catch(e=>setError(e.message));
  useEffect(()=>{load()},[]);
  async function create(e:FormEvent<HTMLFormElement>){
    e.preventDefault();setBusy(true);setError("");setMessage("");const form=e.currentTarget,data=new FormData(form);
    try{await api("/admin/users",{method:"POST",body:JSON.stringify({name:data.get("name"),email:data.get("email"),password:data.get("password"),role:data.get("role")})});form.reset();setMessage("Account created. Give the temporary password directly to the user.");await load()}catch(e){setError(e instanceof Error?e.message:"Unable to create account")}finally{setBusy(false)}
  }
  async function toggle(user:User){setError("");try{await api(`/admin/users/${user.id}`,{method:"PATCH",body:JSON.stringify({is_active:!user.is_active})});await load()}catch(e){setError(e instanceof Error?e.message:"Unable to update account")}}
  async function resetPassword(e:FormEvent<HTMLFormElement>,user:User){e.preventDefault();setError("");setMessage("");const form=e.currentTarget,data=new FormData(form);try{await api(`/admin/users/${user.id}`,{method:"PATCH",body:JSON.stringify({password:data.get("password")})});form.reset();setMessage(`Password reset for ${user.name}.`)}catch(e){setError(e instanceof Error?e.message:"Unable to reset password")}}
  return <><h1 className="text-3xl font-bold">Account management</h1><p className="text-slate-500 mt-2">Give every administrator and viewer their own account. Passwords are stored securely as hashes.</p>
    <form onSubmit={create} className="card p-6 mt-6 grid md:grid-cols-2 xl:grid-cols-5 gap-4 items-end"><label className="label">Full name<input className="input mt-1" name="name" required minLength={2}/></label><label className="label">Institutional email<input className="input mt-1" name="email" type="email" required/></label><label className="label">Temporary password<input className="input mt-1" name="password" type="password" required minLength={12} autoComplete="new-password"/><span className="block font-normal text-xs mt-1">At least 12 characters</span></label><label className="label">Access level<select className="input mt-1" name="role" defaultValue="viewer"><option value="viewer">Viewer — read only</option><option value="reviewer">Reviewer — verify records</option><option value="admin">Administrator — full access</option></select></label><button className="btn" disabled={busy}>{busy?"Creating…":"Create account"}</button></form>
    {error&&<p role="alert" className="bg-red-50 text-red-700 p-3 rounded-lg mt-4">{error}</p>}{message&&<p className="bg-emerald-50 text-emerald-800 p-3 rounded-lg mt-4">{message}</p>}
    <div className="card overflow-auto mt-6"><table className="table"><thead><tr><th>Person</th><th>Email</th><th>Access</th><th>Status</th><th>Password reset</th><th>Action</th></tr></thead><tbody>{users.map(user=><tr key={user.id}><td className="font-bold">{user.name}</td><td>{user.email}</td><td className="capitalize">{user.role}</td><td><span className="badge">{user.is_active?"Active":"Inactive"}</span></td><td><form className="flex gap-2 min-w-[280px]" onSubmit={e=>resetPassword(e,user)}><input className="input" name="password" type="password" placeholder="New temporary password" minLength={12} required autoComplete="new-password"/><button className="btn btn-secondary text-sm">Reset</button></form></td><td><button className="btn btn-secondary text-sm" type="button" onClick={()=>toggle(user)}>{user.is_active?"Deactivate":"Activate"}</button></td></tr>)}</tbody></table></div>
  </>;
}
