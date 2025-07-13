import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'FUB Follow-up Assistant - AI-Powered Real Estate Follow-ups',
  description: 'Boost your Follow Up Boss productivity with AI-powered follow-up suggestions and automated note creation.',
  keywords: 'Follow Up Boss, real estate, AI, CRM, follow-up, automation',
  authors: [{ name: 'FUB Assistant Team' }],
  openGraph: {
    title: 'FUB Follow-up Assistant',
    description: 'AI-powered follow-up suggestions for Follow Up Boss',
    type: 'website',
    url: 'https://fub-assistant.com',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'FUB Follow-up Assistant',
    description: 'AI-powered follow-up suggestions for Follow Up Boss',
  }
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={`${inter.className} antialiased`}>
        {children}
      </body>
    </html>
  )
} 