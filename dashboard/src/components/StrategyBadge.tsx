import { STRATEGY_STYLE } from "@/lib/colors";
import type { StrategyCode } from "@/lib/types";

export function StrategyBadge({ code, withEmoji = false }: { code: StrategyCode; withEmoji?: boolean }) {
  const s = STRATEGY_STYLE[code];
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-xs font-medium ${s.bg} ${s.text}`}
    >
      {withEmoji ? <span aria-hidden>{s.emoji}</span> : null}
      <span>{s.label}</span>
    </span>
  );
}
