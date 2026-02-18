import { useState, useCallback } from 'react'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export interface Product {
  id: string
  name: string
  description: string
  price: string
  image_url: string
  rating?: number | null
  review_count?: number | null
  url?: string
  specs_text?: string
  reviews_json?: string
}

export interface Message {
  role: 'user' | 'assistant'
  content: string
  products?: Product[]
}

export interface ChatResponse {
  response: string
  products: Product[]
  intent: string
  session_id?: string | null
}

export function useAgent() {
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [sessionId, setSessionId] = useState<string | null>(null)

  const sendMessage = useCallback(
    async (content: string, imageBase64?: string | null) => {
      const messagesSnapshot = messages
      if (!content.trim() && !imageBase64) return

      const userMessage: Message = {
        role: 'user',
        content: content.trim() || (imageBase64 ? 'Find products matching this image' : ''),
      }
      setMessages((prev) => [...prev, userMessage])
      setLoading(true)
      setError(null)

      try {
        const historyForApi = messagesSnapshot.map((m) => ({
          role: m.role,
          content: m.content,
        }))
        const lastAssistantWithProducts = [...messagesSnapshot].reverse().find(
          (m) => m.role === 'assistant' && m.products && m.products.length > 0
        )
        const res = await fetch(`${API_URL}/api/chat`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message: content.trim() || 'Find products matching this image',
            image_base64: imageBase64 || null,
            session_id: sessionId,
            history: historyForApi,
            previous_products: lastAssistantWithProducts?.products ?? [],
          }),
        })

        if (!res.ok) {
          const err = await res.json().catch(() => ({}))
          throw new Error(err.detail || `Request failed: ${res.status}`)
        }

        const data: ChatResponse = await res.json()
        if (data.session_id) setSessionId(data.session_id)

        const assistantMessage: Message = {
          role: 'assistant',
          content: data.response,
          products: data.products?.length ? data.products : undefined,
        }
        setMessages((prev) => [...prev, assistantMessage])
      } catch (e) {
        const errMsg = e instanceof Error ? e.message : 'Something went wrong'
        setError(errMsg)
        setMessages((prev) => [
          ...prev,
          { role: 'assistant', content: `Error: ${errMsg}` },
        ])
      } finally {
        setLoading(false)
      }
    },
    [messages, sessionId]
  )

  const startNewChat = useCallback(() => {
    setMessages([])
    setSessionId(null)
    setError(null)
  }, [])

  return { messages, loading, error, sendMessage, startNewChat }
}
