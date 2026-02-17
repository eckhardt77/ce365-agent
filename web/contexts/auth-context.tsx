'use client'

/**
 * TechCare Bot - Auth Context
 * Global Authentication State
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { User } from '@/types'
import { api } from '@/lib/api'

interface AuthContextType {
  user: User | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, name: string, company?: string) => Promise<void>
  logout: () => void
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  // Load user on mount
  useEffect(() => {
    loadUser()
  }, [])

  async function loadUser() {
    try {
      const userData = await api.getMe()
      setUser(userData)
    } catch (error) {
      // Token invalid oder nicht vorhanden
      api.setToken(null)
      setUser(null)
    } finally {
      setLoading(false)
    }
  }

  async function login(email: string, password: string) {
    const response = await api.login(email, password)
    setUser(response.user)
  }

  async function register(email: string, password: string, name: string, company?: string) {
    const response = await api.register(email, password, name, company)
    setUser(response.user)
  }

  function logout() {
    api.logout()
    setUser(null)
  }

  async function refreshUser() {
    await loadUser()
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
