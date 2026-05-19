import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import favicon from './assets/favicon-32x32.png'

const existingIcon = document.querySelector("link[rel~='icon']")
if (existingIcon) {
  existingIcon.href = favicon
} else {
  const icon = document.createElement('link')
  icon.rel = 'icon'
  icon.type = 'image/png'
  icon.href = favicon
  document.head.appendChild(icon)
}

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
