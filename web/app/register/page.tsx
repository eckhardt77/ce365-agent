'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/auth-context'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useToast } from '@/hooks/use-toast'
import { Loader2, Wrench } from 'lucide-react'

export default function RegisterPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')
  const [company, setCompany] = useState('')
  const [loading, setLoading] = useState(false)
  const { register } = useAuth()
  const router = useRouter()
  const { toast } = useToast()

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)

    try {
      await register(email, password, name, company || undefined)
      toast({
        title: 'Registrierung erfolgreich',
        description: 'Willkommen bei TechCare Bot!',
      })
      router.push('/dashboard')
    } catch (error: any) {
      toast({
        title: 'Registrierung fehlgeschlagen',
        description: error.message,
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center p-8 bg-background">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <div className="inline-flex items-center gap-2 mb-4">
            <Wrench className="h-8 w-8 text-primary" />
            <h1 className="text-2xl font-bold">TechCare Bot</h1>
          </div>
          <h2 className="text-xl font-semibold mb-2">Account erstellen</h2>
          <p className="text-muted-foreground">
            Erstelle deinen TechCare Account
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="name">Name *</Label>
            <Input
              id="name"
              type="text"
              placeholder="Max Mustermann"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              disabled={loading}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="email">E-Mail *</Label>
            <Input
              id="email"
              type="email"
              placeholder="name@firma.de"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              disabled={loading}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="company">Firma (optional)</Label>
            <Input
              id="company"
              type="text"
              placeholder="Meine Firma GmbH"
              value={company}
              onChange={(e) => setCompany(e.target.value)}
              disabled={loading}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="password">Passwort *</Label>
            <Input
              id="password"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
              disabled={loading}
            />
            <p className="text-xs text-muted-foreground">
              Mindestens 8 Zeichen, Groß-/Kleinbuchstaben und Zahlen
            </p>
          </div>

          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Registrierung läuft...
              </>
            ) : (
              'Account erstellen'
            )}
          </Button>
        </form>

        <div className="mt-8 text-center text-sm text-muted-foreground">
          <p>Bereits registriert?</p>
          <a href="/" className="text-primary hover:underline font-medium">
            Zur Anmeldung
          </a>
        </div>
      </div>
    </div>
  )
}
