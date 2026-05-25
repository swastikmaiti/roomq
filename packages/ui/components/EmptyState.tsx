export function EmptyState({ title, hint }: { title: string; hint?: string }) {
  return (
    <div className="flex min-h-[40vh] flex-col items-center justify-center text-center text-neutral-500">
      <p className="text-lg font-medium">{title}</p>
      {hint && <p className="mt-1 text-sm">{hint}</p>}
    </div>
  );
}
