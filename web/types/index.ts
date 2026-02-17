// ============================================================================
// TechCare Bot - TypeScript Types
// ============================================================================

export interface User {
  id: string
  email: string
  name: string
  company: string | null
  is_active: boolean
  is_admin: boolean
  repairs_this_month: number
  created_at: string
  last_login_at: string | null
}

export interface AuthToken {
  access_token: string
  token_type: string
  user: User
}

export type ConversationState =
  | 'idle'
  | 'audit'
  | 'analysis'
  | 'plan_ready'
  | 'locked'
  | 'executing'
  | 'completed'
  | 'failed'

export interface Conversation {
  id: string
  user_id: string
  title: string
  problem_description: string | null
  state: ConversationState
  os_type: string | null
  os_version: string | null
  created_at: string
  updated_at: string
  completed_at: string | null
  message_count?: number
}

export interface ConversationListResponse {
  conversations: Conversation[]
  total: number
  page: number
  page_size: number
}

export type MessageRole = 'user' | 'assistant' | 'system'

export interface Message {
  id: string
  conversation_id: string
  role: MessageRole
  content: string
  sequence: number
  input_tokens: number | null
  output_tokens: number | null
  created_at: string
}

export interface ChatRequest {
  message: string
  conversation_id?: string
}

export interface ChatStreamChunk {
  type: 'content' | 'tool_use' | 'tool_executing' | 'tool_result' | 'done' | 'error'
  content?: string
  tool_name?: string
  tool_input?: Record<string, any>
  success?: boolean
  output?: string
  error?: string
  conversation_id?: string
}

export interface ToolCall {
  id: string
  conversation_id: string
  tool_name: string
  tool_type: string
  tool_input: Record<string, any>
  tool_output: string | null
  success: boolean
  error_message: string | null
  execution_time_ms: number | null
  requires_approval: boolean
  approved: boolean
  created_at: string
  completed_at: string | null
}

export interface Case {
  id: string
  problem_description: string
  problem_keywords: string[]
  root_cause: string
  os_type: string
  os_version: string | null
  solution_plan: string
  solution_steps: Record<string, any>[]
  tools_used: string[]
  success: boolean
  execution_time_minutes: number | null
  complexity_score: number | null
  reuse_count: number
  success_count: number
  success_rate: number
  created_at: string
  last_reused_at: string | null
}

export interface CaseSearchResult {
  case: Case
  similarity: number
}

export interface ApiError {
  detail: string
  error?: string
}
