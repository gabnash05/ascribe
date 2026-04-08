import axios from 'axios'
import { supabase } from '@/lib/supabase'

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? '/api/v1',
})

apiClient.interceptors.request.use(async (config) => {
  try {
    const {
      data: { session },
      error,
    } = await supabase.auth.getSession()

    if (error) {
      console.warn('Supabase session error:', error.message)
      return config
    }

    if (session?.access_token) {
      config.headers.Authorization = `Bearer ${session.access_token}`
    }
  } catch (error) {
    console.warn('Failed to retrieve auth session:', error)
  }

  return config
})
