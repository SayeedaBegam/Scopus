import "./globals.css";import Shell from "@/components/Shell";
export const metadata={title:"UTN Research Partnerships",description:"International joint publication analytics"};
export default function Layout({children}:{children:React.ReactNode}){return <html lang="en"><body><Shell>{children}</Shell></body></html>}
