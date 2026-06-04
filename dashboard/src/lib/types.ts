export type Aspect = "rasa" | "harga" | "pelayanan";
export type Label = "tidak_disebut" | "positif" | "negatif" | "netral";
export type StrategyCode = "ATTACK" | "FIX" | "DEFEND" | "PROMOTE" | "MONITOR" | "NO_DATA";

export interface AspectScores {
  positif: number;
  negatif: number;
  netral: number;
  tidak_disebut: number;
  volume: number;
  decisive: number;
  positive_share: number | null;
  net_sentiment: number | null;
}

export interface UmkmSnapshot {
  _count: number;
  aspects: Record<Aspect, AspectScores>;
  strategies: Record<Aspect, StrategyCode>;
  headlines: string[];
}

export interface MarketMedian {
  median_positive_share: number | null;
  median_net_sentiment: number | null;
  n_umkm: number;
}

export interface Snapshot {
  total_reviews: number;
  umkm_count: number;
  market: Record<Aspect, MarketMedian>;
  per_umkm: Record<string, UmkmSnapshot>;
  min_volume_threshold: number;
  thresholds: { gap_big: number; low_share: number; high_share: number };
}

export interface RecommendationAction {
  aspect: Aspect;
  code: StrategyCode;
  priority: number;
  positive_share: number | null;
  market_share: number | null;
  volume: number;
  rationale: string;
  actionable: string[];
}

export interface UmkmRecommendation {
  summary: string;
  actions: RecommendationAction[];
  review_count: number;
}

export interface Recommendations {
  per_umkm: Record<string, UmkmRecommendation>;
  market: Record<Aspect, MarketMedian>;
}

export interface Prediction {
  review_id: string;
  umkm_id: string;
  rating: string;
  rasa: Label;
  harga: Label;
  pelayanan: Label;
  text: string;
}

export const ASPECTS: Aspect[] = ["rasa", "harga", "pelayanan"];

export const UMKM_DISPLAY_NAME: Record<string, string> = {
  nasi_goreng_surya: "Nasi Goreng Surya",
  nasi_goreng_komdak: "Nasi Goreng Komdak",
  nasi_goreng_pemuda: "Nasi Goreng Pemuda",
  nasi_goreng_semalam_suntuk: "Nasi Goreng Semalam Suntuk",
  nasi_goreng_pandu: "Nasi Goreng Pandu",
  istana_nasi_goreng: "Istana Nasi Goreng",
  nasi_olengg: "Nasi Olengg",
  naste: "NASTE",
  nasi_goreng_wak_ribut: "Nasi Goreng Wak Ribut",
};

export function umkmName(id: string): string {
  return UMKM_DISPLAY_NAME[id] ?? id;
}
