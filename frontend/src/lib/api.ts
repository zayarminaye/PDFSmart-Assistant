/**
 * API client for PDFSmart Assistant backend
 */
import axios from 'axios'
import type { DocumentAnalysis, FormField } from '@/types'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Types
export interface DocumentUploadResponse {
  document_id: string
  filename: string
  file_size: number
  upload_timestamp: string
  expires_at: string
}

export type FormAnalysisResponse = DocumentAnalysis
export type { FormField }

export interface FillFormResponse {
  document_id: string
  filled_document_url: string
  fields_filled: number
  fields_total: number
  processing_time_ms: number
}

export interface ExtractionResponse {
  document_id: string
  extracted_content: any
  content_type: string
  download_url?: string
  processing_time_ms: number
}

// API Methods
export const uploadPDF = async (file: File): Promise<DocumentUploadResponse> => {
  const formData = new FormData()
  formData.append('file', file)

  const response = await api.post('/api/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })

  return response.data
}

export const analyzePDF = async (documentId: string): Promise<FormAnalysisResponse> => {
  const response = await api.post(`/api/analyze/${documentId}`)
  return response.data
}

export const fillForm = async (
  documentId: string,
  instructions: string
): Promise<FillFormResponse> => {
  const response = await api.post('/api/form/fill', {
    document_id: documentId,
    instructions,
  })
  return response.data
}

export const extractContent = async (
  documentId: string,
  extractionQuery: string,
  outputFormat: string = 'text',
  pages?: number[]
): Promise<ExtractionResponse> => {
  const response = await api.post('/api/extract/extract', {
    document_id: documentId,
    extraction_query: extractionQuery,
    output_format: outputFormat,
    pages,
  })
  return response.data
}

export const extractTables = async (
  documentId: string,
  pages?: string
): Promise<any> => {
  const url = pages ? `/api/extract/tables/${documentId}?pages=${pages}` : `/api/extract/tables/${documentId}`
  const response = await api.get(url)
  return response.data
}

export const extractText = async (
  documentId: string,
  pages?: string
): Promise<any> => {
  const url = pages ? `/api/extract/text/${documentId}?pages=${pages}` : `/api/extract/text/${documentId}`
  const response = await api.get(url)
  return response.data
}

export const healthCheck = async (): Promise<any> => {
  const response = await api.get('/api/health')
  return response.data
}

export default api
