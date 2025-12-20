import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { ClubThemeProvider } from './config/ClubThemeProvider'
import './index.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <ClubThemeProvider>
        <App />
      </ClubThemeProvider>
    </BrowserRouter>
  </StrictMode>,
)
