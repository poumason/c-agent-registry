import { apiClient } from "./client";
import type { Review, ReviewerCandidate, ReviewQueueResponse, ReviewResult, ReviewSummary } from "./types";

export async function listReviewerCandidates(): Promise<ReviewerCandidate[]> {
  const { data } = await apiClient.get<ReviewerCandidate[]>("/reviewers");
  return data;
}

export interface ReviewQueueParams {
  status?: ReviewResult;
  limit?: number;
  offset?: number;
}

export async function listReviewQueue(params: ReviewQueueParams = {}): Promise<ReviewQueueResponse> {
  const { data } = await apiClient.get<ReviewQueueResponse>("/reviews", { params });
  return data;
}

export async function getReviewSummary(): Promise<ReviewSummary> {
  const { data } = await apiClient.get<ReviewSummary>("/admin/review-summary");
  return data;
}

export async function listVersionReviews(versionSlug: string): Promise<Review[]> {
  const { data } = await apiClient.get<Review[]>(`/versions/${versionSlug}/reviews`);
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
