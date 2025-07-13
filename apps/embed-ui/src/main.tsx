import React from 'react'
import ReactDOM from 'react-dom/client'
import { setApiBaseUrl } from '@fub-assistant/shared'
import App from './App.tsx'
import './index.css'

// Configure API base URL
setApiBaseUrl('https://fub-followup-assistant-production.up.railway.app')

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
) 