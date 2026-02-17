'use client'

import { useAuth } from '@/contexts/auth-context'
import { Button } from '@/components/ui/button'
import { Plus, Wrench, TrendingUp, CheckCircle2 } from 'lucide-react'
import { useRouter } from 'next/navigation'

export default function DashboardPage() {
  const { user } = useAuth()
  const router = useRouter()

  return (
    <div className="flex-1 overflow-y-auto p-8">
      <div className="max-w-4xl mx-auto">
        {/* Welcome */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">
            Willkommen zurück, {user?.name}!
          </h1>
          <p className="text-muted-foreground">
            Bereit für einen neuen Fall?
          </p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <div className="p-6 border rounded-lg bg-card">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-muted-foreground">
                Reparaturen diesen Monat
              </span>
              <Wrench className="h-5 w-5 text-muted-foreground" />
            </div>
            <div className="text-3xl font-bold">
              {user?.repairs_this_month || 0}
            </div>
          </div>

          <div className="p-6 border rounded-lg bg-card">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-muted-foreground">
                Erfolgsquote
              </span>
              <TrendingUp className="h-5 w-5 text-muted-foreground" />
            </div>
            <div className="text-3xl font-bold">95%</div>
          </div>

          <div className="p-6 border rounded-lg bg-card">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-muted-foreground">
                Abgeschlossene Fälle
              </span>
              <CheckCircle2 className="h-5 w-5 text-muted-foreground" />
            </div>
            <div className="text-3xl font-bold">0</div>
          </div>
        </div>

        {/* Quick Start */}
        <div className="border rounded-lg p-8 bg-card text-center">
          <Wrench className="h-12 w-12 text-primary mx-auto mb-4" />
          <h2 className="text-2xl font-bold mb-2">Neuen Fall starten</h2>
          <p className="text-muted-foreground mb-6">
            Beschreibe das Problem und lass TechCare Bot die Diagnose durchführen
          </p>
          <Button
            size="lg"
            onClick={() => router.push('/dashboard/chat/new')}
          >
            <Plus className="mr-2 h-5 w-5" />
            Neuer Fall
          </Button>
        </div>

        {/* Recent Cases */}
        <div className="mt-8">
          <h2 className="text-xl font-bold mb-4">Letzte Fälle</h2>
          <div className="text-sm text-muted-foreground">
            Noch keine Fälle vorhanden
          </div>
        </div>
      </div>
    </div>
  )
}
