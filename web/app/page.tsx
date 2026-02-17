'use client'

/**
 * TechCare Bot - Landing / Login Page
 */

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/auth-context'
import { LoginForm } from '@/components/auth/login-form'
import { Wrench } from 'lucide-react'

export default function Home() {
  const { user, loading } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!loading && user) {
      router.push('/dashboard')
    }
  }, [user, loading, router])

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary" />
      </div>
    )
  }

  return (
    <div className="flex min-h-screen">
      {/* Left Side - Branding */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-blue-600 to-blue-800 p-12 flex-col justify-between text-white">
        <div>
          <div className="flex items-center gap-3 mb-8">
            <Wrench className="h-10 w-10" />
            <h1 className="text-3xl font-bold">TechCare Bot</h1>
          </div>
          <h2 className="text-4xl font-bold mb-4">
            AI-powered<br />IT-Wartungsassistent
          </h2>
          <p className="text-xl text-blue-100 mb-8">
            Intelligente Diagnose und Reparatur für Windows & macOS Systeme
          </p>
          <div className="space-y-4">
            <div className="flex items-start gap-3">
              <div className="mt-1 h-6 w-6 rounded-full bg-blue-500 flex items-center justify-center text-sm">
                ✓
              </div>
              <div>
                <h3 className="font-semibold mb-1">Natürlich kommunizieren</h3>
                <p className="text-blue-100">Beschreibe das Problem in natürlicher Sprache</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className="mt-1 h-6 w-6 rounded-full bg-blue-500 flex items-center justify-center text-sm">
                ✓
              </div>
              <div>
                <h3 className="font-semibold mb-1">Sicher reparieren</h3>
                <p className="text-blue-100">Freigabe-basierter Workflow mit Audit-Trail</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className="mt-1 h-6 w-6 rounded-full bg-blue-500 flex items-center justify-center text-sm">
                ✓
              </div>
              <div>
                <h3 className="font-semibold mb-1">Aus Fällen lernen</h3>
                <p className="text-blue-100">Shared Learning für das ganze Team</p>
              </div>
            </div>
          </div>
        </div>
        <div className="text-sm text-blue-200">
          © 2026 Carsten Eckhardt / Eckhardt-Marketing
        </div>
      </div>

      {/* Right Side - Login Form */}
      <div className="flex-1 flex items-center justify-center p-8 bg-background">
        <div className="w-full max-w-md">
          <div className="lg:hidden mb-8 text-center">
            <div className="inline-flex items-center gap-2 mb-4">
              <Wrench className="h-8 w-8 text-primary" />
              <h1 className="text-2xl font-bold">TechCare Bot</h1>
            </div>
            <p className="text-muted-foreground">AI-powered IT-Wartungsassistent</p>
          </div>

          <LoginForm />

          <div className="mt-8 text-center text-sm text-muted-foreground">
            <p>Noch kein Account?</p>
            <a href="/register" className="text-primary hover:underline font-medium">
              Jetzt registrieren
            </a>
          </div>
        </div>
      </div>
    </div>
  )
}
