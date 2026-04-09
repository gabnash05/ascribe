import { apiClient } from './client'
import type {
  SearchResponse,
  SummarizeRequest,
  FlashcardRequest,
  QuizRequest,
  AIResponse,
} from '@/types'

export const searchApi = {
  search: (vaultId: string, query: string, top_k = 10) =>
    apiClient
      .post<SearchResponse>(`/vaults/${vaultId}/search`, { query, top_k })
      .then((r) => r.data),
}

export const aiApi = {
  summarize: (vaultId: string, body: SummarizeRequest) =>
    apiClient.post<AIResponse>(`/vaults/${vaultId}/summarize`, body).then((r) => r.data),
  generateFlashcards: (vaultId: string, body: FlashcardRequest) =>
    apiClient.post<AIResponse>(`/vaults/${vaultId}/generate-qa`, body).then((r) => r.data),
  generateQuiz: (vaultId: string, body: QuizRequest) =>
    apiClient.post<AIResponse>(`/vaults/${vaultId}/quiz`, body).then((r) => r.data),
}
