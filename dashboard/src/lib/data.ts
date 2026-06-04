import snapshotJson from "@/data/snapshot.json";
import recommendationsJson from "@/data/recommendations.json";
import predictionsJson from "@/data/predictions.json";
import type { Snapshot, Recommendations, Prediction } from "./types";

export const snapshot = snapshotJson as unknown as Snapshot;
export const recommendations = recommendationsJson as unknown as Recommendations;
export const predictions = predictionsJson as unknown as Prediction[];

export const umkmIds = Object.keys(snapshot.per_umkm).sort();
