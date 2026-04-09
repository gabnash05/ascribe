export interface FlashCard {
  question: string
  answer: string
  difficulty: 'easy' | 'medium' | 'hard'
}

export interface QuizQuestion {
  question: string
  options: string[] // ["A. ...", "B. ...", "C. ...", "D. ..."]
  correct: 'A' | 'B' | 'C' | 'D'
  explanation: string[]
}

export interface FlashcardRequest {
  count?: number
  file_ids?: string[]
}

export interface QuizRequest {
  count?: number
  file_ids?: string[]
}

export interface SummarizeRequest {
  file_ids?: string[] | null
}
