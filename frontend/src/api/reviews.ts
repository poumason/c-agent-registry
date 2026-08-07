import { apiClient } from "./client";
import type { Review, ReviewerCandidate, ReviewResult } from "./types";

export async function listReviewerCandidates(): Promise<ReviewerCandidate[]> {
  const { data } = await apiClient.get<ReviewerCandidate[]>("/reviewers");
  return data;
}

export async function listMyReviews(pendingOnly = true): Promise<Review[]> {
  const { data } = await apiClient.get<Review[]>("/reviews/mine", {
    params: { pending_only: pendingOnly },
  });
  return data;
}

export async function listVersionReviews(versionSlug: string): Promise<Review[]> {
  const { data } = await apiClient.get<Review[]>(`/versions/${versionSlug}/reviews`);
  return data;
}

export async function getReview(reviewId: string): Promise<Review> {
  const { data } = await apiClient.get<Review>(`/reviews/${reviewId}`);
  return data;
}

export async function decideReview(
  reviewId: string,
  result: Extract<ReviewResult, "approved" | "rejected">,
  comment?: string,
): Promise<Review> {
  const { data } = await apiClient.post<Review>(`/reviews/${reviewId}/decision`, {
    result,
    comment: comment || undefined,
  });
  return data;
}
