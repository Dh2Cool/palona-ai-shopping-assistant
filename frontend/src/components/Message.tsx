import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import type { Message as MessageType, Product } from '../hooks/useAgent'

interface MessageProps {
  message: MessageType
}

function StarRating({ rating }: { rating: number }) {
  const full = Math.floor(rating)
  const empty = 5 - full
  return (
    <span className="star-rating" aria-label={`${rating} out of 5 stars`}>
      <span className="stars-filled">{'★'.repeat(full)}</span>
      <span className="stars-empty">{'☆'.repeat(empty)}</span>
    </span>
  )
}

/** Split description into paragraphs; format with line breaks. */
function formatDescription(text: string) {
  if (!text?.trim()) return null
  const paragraphs = text.split(/\n\n+/).filter((p) => p.trim())
  if (paragraphs.length === 0) return <p>{text}</p>
  return (
    <>
      {paragraphs.map((para, i) => (
        <p key={i}>
          {para.split('\n').map((line, j) => (
            <span key={j}>
              {j > 0 && <br />}
              {line}
            </span>
          ))}
        </p>
      ))}
    </>
  )
}

/** Parse specs into key-value rows. Split by newline only to avoid breaking values like "(20,231)". */
function formatSpecs(text: string) {
  if (!text?.trim()) return null
  const raw = text.replace(/\r/g, '')
  const lines = raw.split(/\n/).map((l) => l.trim()).filter(Boolean)
  const items: { key: string; value: string }[] = []
  for (const line of lines) {
    const dashMatch = line.match(/^(.+?)\s+[-–—]\s+(.+)$/)
    const colonMatch = line.match(/^(.+?):\s*(.+)$/)
    const valueAfterSpace = line.match(/^(.+?)\s+(\d.+)$/) // "Product Dimensions 5 x 4.5..."
    const singleWord = line.match(/^(\S+)\s+(.+)$/) // "ASIN B004N7NFSK"
    if (dashMatch) {
      items.push({ key: dashMatch[1].trim(), value: dashMatch[2].trim() })
    } else if (colonMatch) {
      items.push({ key: colonMatch[1].trim(), value: colonMatch[2].trim() })
    } else if (valueAfterSpace) {
      items.push({ key: valueAfterSpace[1].trim(), value: valueAfterSpace[2].trim() })
    } else if (singleWord) {
      items.push({ key: singleWord[1].trim(), value: singleWord[2].trim() })
    } else {
      items.push({ key: line, value: '' })
    }
  }
  return (
    <dl className="specs-list">
      {items.map((item, i) => (
        <div key={i} className="specs-row">
          <dt>{item.key}</dt>
          <dd>{item.value || '—'}</dd>
        </div>
      ))}
    </dl>
  )
}

function ProductModal({
  product,
  onClose,
}: {
  product: Product
  onClose: () => void
}) {
  const hasRating = product.rating != null && product.rating > 0
  const reviewLabel =
    product.review_count != null && product.review_count > 0
      ? product.review_count.toLocaleString()
      : null

  let reviewsPreview = ''
  try {
    const parsed = product.reviews_json ? JSON.parse(product.reviews_json) : null
    if (Array.isArray(parsed) && parsed.length > 0) {
      reviewsPreview = parsed
        .slice(0, 3)
        .map((r: { body?: string; text?: string }) => r?.body || r?.text || '')
        .filter(Boolean)
        .join('\n\n')
    } else if (typeof parsed === 'string') {
      reviewsPreview = parsed.slice(0, 500)
    }
  } catch {
    reviewsPreview = (product.reviews_json || '').slice(0, 500)
  }

  return (
    <div className="product-modal-overlay" onClick={onClose}>
      <div className="product-modal" onClick={(e) => e.stopPropagation()}>
        <div className="product-modal-header">
          <h2 className="product-modal-title">{product.name}</h2>
          <button
            type="button"
            className="product-modal-close"
            onClick={onClose}
            aria-label="Close"
          >
            ×
          </button>
        </div>
        <div className="product-modal-scroll">
          <img
            src={product.image_url}
            alt={product.name}
            className="product-modal-image"
          />
          <div className="product-modal-body">
            <span className="modal-price">{product.price}</span>
            {hasRating && reviewLabel != null && (
              <div className="modal-section">
                <div className="modal-section-title">Rating</div>
                <div className="modal-section-content">
                  <StarRating rating={product.rating!} /> ({reviewLabel} reviews)
                </div>
              </div>
            )}
            <div className="modal-section">
              <div className="modal-section-title">Description</div>
              <div className="modal-section-content">
                {formatDescription(product.description) || product.description}
              </div>
            </div>
            {product.specs_text && (
              <div className="modal-section">
                <div className="modal-section-title">Specifications</div>
                <div className="modal-section-content specs-content">
                  {formatSpecs(product.specs_text)}
                </div>
              </div>
            )}
            {reviewsPreview && (
              <div className="modal-section">
                <div className="modal-section-title">Review snippets</div>
                <div className="modal-section-content">
                  {formatDescription(reviewsPreview) || reviewsPreview}
                </div>
              </div>
            )}
            {product.url && (
              <a
                href={product.url}
                target="_blank"
                rel="noopener noreferrer"
                className="modal-link"
              >
                View on Amazon
              </a>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

function ProductCard({ product }: { product: Product }) {
  const [modalOpen, setModalOpen] = useState(false)
  const hasRating = product.rating != null && product.rating > 0
  const reviewLabel =
    product.review_count != null && product.review_count > 0
      ? product.review_count.toLocaleString()
      : null

  return (
    <>
      <div className="product-card">
        <button
          type="button"
          className="product-card-more"
          onClick={(e) => {
            e.stopPropagation()
            setModalOpen(true)
          }}
          aria-label="More info"
          title="View full details"
        >
          ⋮
        </button>
        <div className="product-card-popup">
          <strong>{product.name}</strong>
          <span className="popup-price">{product.price}</span>
          {hasRating && reviewLabel != null && (
            <span className="popup-rating">
              {' ★'.repeat(Math.floor(product.rating!))} ({reviewLabel})
            </span>
          )}
        </div>
        <div className="product-card-image">
          <img src={product.image_url} alt={product.name} loading="lazy" />
        </div>
        <div className="product-card-body">
          <strong className="product-name">{product.name}</strong>
          {hasRating && (
            <div className="product-rating-row">
              <StarRating rating={product.rating!} />
              {reviewLabel != null && (
                <span className="product-review-count">({reviewLabel})</span>
              )}
            </div>
          )}
          <span className="product-price">{product.price}</span>
          <p className="product-description">{product.description}</p>
          {product.url && (
            <a
              href={product.url}
              target="_blank"
              rel="noopener noreferrer"
              className="product-link"
            >
              View on Amazon
            </a>
          )}
        </div>
      </div>
      {modalOpen && (
        <ProductModal product={product} onClose={() => setModalOpen(false)} />
      )}
    </>
  )
}

export function Message({ message }: MessageProps) {
  const isUser = message.role === 'user'

  return (
    <div className={`message ${isUser ? 'user' : 'assistant'}`}>
      <div className="message-avatar">{isUser ? 'You' : 'Palona'}</div>
      <div className="message-content">
        {message.content && (
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {message.content}
          </ReactMarkdown>
        )}
        {message.products && message.products.length > 0 && (
          <div className="product-row">
            {message.products.map((p) => (
              <ProductCard key={p.id} product={p} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
