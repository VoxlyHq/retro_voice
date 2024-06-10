import { useEffect, useState } from 'react'
import { useLocation, Link } from 'wouter'

import { Card, CardFooter, CardDescription, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'

interface User {
  email: string
}

export function HomePage() {
  const [isLoading, setIsLoading] = useState(true)
  const [user, setUser] = useState<User | null>(null)
  const [, setLocation] = useLocation()

  const onSignIn = () => {
    setLocation('/signin')
  }

  const onSignOut = async () => {
    await fetch(`${__BASE_API_URL__}/signout`, { method: 'POST' })
    setUser(null)
  }

  useEffect(() => {
    ;(async () => {
      const response = await fetch(`${__BASE_API_URL__}/user`)
      const data = await response.json()
      if (response.ok) {
        setUser(data)
      }
      setIsLoading(false)
    })()
  }, [])

  return (
    <div className="flex h-screen items-center justify-center">
      <Card className="max-w-xl">
        <CardHeader>
          <CardTitle>Welcome to Retro Voice!</CardTitle>
          <CardDescription>
            {isLoading ? (
              <p>Loading...</p>
            ) : user !== null ? (
              <p>
                You are signed in as <b>{user.email}</b>
              </p>
            ) : (
              <p>Sign in to get started!</p>
            )}
          </CardDescription>
        </CardHeader>
        {user !== null && (
          <CardContent>
            Check out the{' '}
            <Link href="/webrtc" className="underline">
              WebRTC
            </Link>{' '}
            page.
          </CardContent>
        )}
        <CardFooter className="justify-center" style={{ visibility: !isLoading ? 'visible' : 'hidden' }}>
          {user === null ? <Button onClick={onSignIn}>Sign In</Button> : <Button onClick={onSignOut}>Sign Out</Button>}
        </CardFooter>
      </Card>
    </div>
  )
}
