import { ReactNode } from "react";

type PageHeaderProps = {
  title: string;
  description?: string;
  eyebrow?: string;
  actions?: ReactNode;
};

export function PageHeader({ title, description, eyebrow, actions }: PageHeaderProps) {
  return (
    <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
      <div className="min-w-0">
        {eyebrow && (
          <p className="text-[11px] font-semibold uppercase tracking-wider text-brand-blue">
            {eyebrow}
          </p>
        )}
        <h1 className="mt-1 text-[28px] font-semibold tracking-tight text-brand-black">{title}</h1>
        {description && (
          <p className="mt-1.5 max-w-2xl text-sm text-brand-grayMid">{description}</p>
        )}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
    </div>
  );
}
