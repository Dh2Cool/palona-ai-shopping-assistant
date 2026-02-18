import { useRef, useEffect, useState } from 'react'
import { useAgent } from '../hooks/useAgent'
import { Message } from './Message'
import { ImageUpload } from './ImageUpload'

export function Chat() {
  const { messages, loading, warmingUp, error, sendMessage, startNewChat } = useAgent()
  const [input, setInput] = useState('')
  const [attachedImage, setAttachedImage] = useState<string | null>(null)
  const [uploadKey, setUploadKey] = useState(0)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  useEffect(() => { scrollToBottom() }, [messages])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (loading) return
    const content = input.trim() || (attachedImage ? 'Find products matching this image' : '')
    if (!content) return
    sendMessage(content, attachedImage)
    setInput('')
    setAttachedImage(null)
    setUploadKey((k) => k + 1)
  }

  return (
    <div className="chat-container">
      <div className="chat-header">
        <div className="chat-header-left">
          <img src="/logo.svg" alt="Palona" className="chat-logo" />
          <p>AI Shopping Assistant</p>
        </div>
        <button
          type="button"
          onClick={startNewChat}
          className="new-chat-btn"
          title="Start new conversation"
        >
          New chat
        </button>
      </div>

      <div className="messages">
        {messages.length === 0 && (
          <div className="welcome">
            <p>Hi! I'm Palona. I can help you with:</p>
            <ul>
              <li>General chat – ask my name, what I can do</li>
              <li>Product recommendations – e.g. &quot;Recommend a t-shirt for sports&quot;</li>
              <li>Image search – upload an image to find similar products</li>
            </ul>
          </div>
        )}
        {messages.map((msg, i) => (
          <Message key={i} message={msg} />
        ))}
        {loading && (
          <div className="message assistant">
            <div className="message-avatar">Palona</div>
            <div className="message-content">
              <div className="typing">
                {warmingUp ? 'Warming up... (first load takes 1–2 min). Retrying in 60s...' : 'Thinking...'}
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="input-footer">
        {error && <div className="error-banner">{error}</div>}
        <form onSubmit={handleSubmit} className="input-area">
        <ImageUpload
          key={uploadKey}
          onImageSelect={(b64) => setAttachedImage(b64 || null)}
          disabled={loading}
        />
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={attachedImage ? "Image attached – click Send to search by image" : "Ask for recommendations or attach an image..."}
          disabled={loading}
          className="text-input"
        />
        <button type="submit" disabled={loading} className="send-btn">
          Send
        </button>
      </form>
      </div>
    </div>
  )
}
