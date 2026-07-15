"use client";
import Link from "next/link";import {useEffect,useState} from "react";import {usePathname,useRouter} from "next/navigation";import {BarChart3,BookOpen,Download,FileUp,LogOut,ShieldCheck,UserCog,Users} from "lucide-react";import {api,User} from "@/lib/api";
const items=[
  {href:"/professors",label:"Professors",icon:Users},
  {href:"/analytics",label:"Overall analytics",icon:BarChart3},
  {href:"/imports",label:"CSV import",icon:FileUp,roles:["admin"]},
  {href:"/reviews",label:"Needs review",icon:ShieldCheck,roles:["admin","reviewer"]},
  {href:"/downloads",label:"Downloads",icon:Download},
  {href:"/admin/professors",label:"Manage professors",icon:BookOpen,roles:["admin"]},
  {href:"/admin/users",label:"Manage accounts",icon:UserCog,roles:["admin"]},
] as const;
export default function Shell({children}:{children:React.ReactNode}){const path=usePathname(),router=useRouter(),[user,setUser]=useState<User>();useEffect(()=>{if(path!=="/login")api<User>("/auth/me").then(setUser).catch(()=>{})},[path]);if(path==="/login")return children;const visible=items.filter(item=>!("roles" in item)||item.roles.includes(user?.role as never));return <div className="min-h-screen md:grid md:grid-cols-[250px_1fr]"><aside className="bg-utn-navy text-white p-5"><div className="mb-9"><p className="text-xs tracking-[.2em] text-teal-100">UTN</p><h1 className="text-xl font-bold">Research partnerships</h1></div><nav className="space-y-1">{visible.map(({href,label,icon:Icon})=><Link key={label} href={href} className={`flex gap-3 items-center rounded-lg px-3 py-2.5 ${path.startsWith(href)?"bg-white/15":"hover:bg-white/10"}`}><Icon size={18}/>{label}</Link>)}</nav>{user&&<p className="mt-8 text-xs text-teal-100">Signed in as<br/><span className="font-bold text-white">{user.name}</span> · {user.role}</p>}<button className="mt-5 flex gap-2 items-center text-sm text-teal-100" onClick={async()=>{await api("/auth/logout",{method:"POST"});router.push("/login")}}><LogOut size={16}/>Sign out</button></aside><main><header className="bg-white border-b px-6 py-4"><p className="text-sm text-slate-500">UTN / International research collaboration</p></header><div className="p-5 md:p-8 max-w-[1500px]">{children}</div></main></div>}
