import { cn } from "@/lib/utils";
import { type ButtonHTMLAttributes } from "react";
type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "secondary" };
export function Button({ className, variant = "primary", ...props }: ButtonProps) {
  return <button className={cn("inline-flex items-center justify-center rounded-lg px-4 py-2 text-sm font-semibold transition", variant === "primary" ? "bg-brand-blue text-white hover:bg-[#0f6fab]" : "border border-slate-200 bg-white text-brand-grayMid hover:bg-slate-50", className)} {...props} />;
}