import axios from 'axios'
import toast from 'react-hot-toast'

const api = axios.create({
  baseURL: '/api',
  timeout: 120000,
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    const msg = err.response?.data?.detail || err.message || 'An error occurred'
    toast.error(msg)
    return Promise.reject(err)
  }
)

export default api
