/**
 * TechCare Bot - API Client
 * Fetch wrapper für Backend API
 */

import {
  AuthToken,
  User,
  Conversation,
  ConversationListResponse,
  Message,
  Case,
  CaseSearchResult,
  ApiError
} from '@/types'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

class ApiClient {
  private baseUrl: string
  private token: string | null = null

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl
    // Load token from localStorage (client-side only)
    if (typeof window !== 'undefined') {
      this.token = localStorage.getItem('auth_token')
    }
  }

  setToken(token: string | null) {
    this.token = token
    if (typeof window !== 'undefined') {
      if (token) {
        localStorage.setItem('auth_token', token)
      } else {
        localStorage.removeItem('auth_token')
      }
    }
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    }

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`
    }

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers,
    })

    if (!response.ok) {
      const error: ApiError = await response.json()
      throw new Error(error.detail || error.error || 'API Error')
    }

    return response.json()
  }

  // ========================================================================
  // AUTH
  // ========================================================================

  async register(email: string, password: string, name: string, company?: string): Promise<AuthToken> {
    const token = await this.request<AuthToken>('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, name, company }),
    })
    this.setToken(token.access_token)
    return token
  }

  async login(email: string, password: string): Promise<AuthToken> {
    const token = await this.request<AuthToken>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    })
    this.setToken(token.access_token)
    return token
  }

  async getMe(): Promise<User> {
    return this.request<User>('/api/auth/me')
  }

  logout() {
    this.setToken(null)
  }

  // ========================================================================
  // CONVERSATIONS
  // ========================================================================

  async createConversation(title: string, problem_description?: string): Promise<Conversation> {
    return this.request<Conversation>('/api/chat/conversations', {
      method: 'POST',
      body: JSON.stringify({ title, problem_description }),
    })
  }

  async getConversations(page = 1, page_size = 20): Promise<ConversationListResponse> {
    return this.request<ConversationListResponse>(
      `/api/chat/conversations?page=${page}&page_size=${page_size}`
    )
  }

  async getConversation(id: string): Promise<Conversation> {
    return this.request<Conversation>(`/api/chat/conversations/${id}`)
  }

  async getMessages(conversationId: string): Promise<Message[]> {
    return this.request<Message[]>(`/api/chat/conversations/${conversationId}/messages`)
  }

  async deleteConversation(id: string): Promise<void> {
    await this.request(`/api/chat/conversations/${id}`, {
      method: 'DELETE',
    })
  }

  // ========================================================================
  // CHAT STREAMING
  // ========================================================================

  async *chatStream(conversationId: string, message: string): AsyncGenerator<any, void, unknown> {
    const response = await fetch(
      `${this.baseUrl}/api/chat/conversations/${conversationId}/messages/stream`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.token}`,
        },
        body: JSON.stringify({ message }),
      }
    )

    if (!response.ok) {
      throw new Error('Chat stream failed')
    }

    const reader = response.body?.getReader()
    const decoder = new TextDecoder()

    if (!reader) {
      throw new Error('No reader available')
    }

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const chunk = decoder.decode(value)
      const lines = chunk.split('\n')

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6)
          try {
            const parsed = JSON.parse(data)
            yield parsed
          } catch (e) {
            console.error('Failed to parse SSE data:', e)
          }
        }
      }
    }
  }

  // ========================================================================
  // LEARNING
  // ========================================================================

  async searchCases(
    problem_description: string,
    os_type?: string,
    limit = 5
  ): Promise<CaseSearchResult[]> {
    return this.request<CaseSearchResult[]>('/api/learning/cases/search', {
      method: 'POST',
      body: JSON.stringify({ problem_description, os_type, limit }),
    })
  }

  async getCase(id: string): Promise<Case> {
    return this.request<Case>(`/api/learning/cases/${id}`)
  }

  // ========================================================================
  // HEALTH
  // ========================================================================

  async health(): Promise<any> {
    return this.request('/api/health')
  }
}

export const api = new ApiClient(API_URL)
