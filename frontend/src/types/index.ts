/**
 * Shared types for PDFSmart Assistant frontend
 */

export interface UploadedDocument {
  id: string
  filename: string
  fileSize: number
  uploadTimestamp: string
  expiresAt: string
}

export interface FormField {
  field_name: string
  field_type: 'text' | 'checkbox' | 'radio' | 'signature' | 'date'
  coordinates: {
    x: number
    y: number
    width: number
    height: number
  }
  page_number: number
  current_value?: string
}

export interface DocumentAnalysis {
  document_id: string
  total_pages: number
  detected_fields: FormField[]
  is_scanned: boolean
  ocr_engine_used?: string
}

export interface ProcessingState {
  isUploading: boolean
  isAnalyzing: boolean
  isProcessing: boolean
  error: string | null
}

export type OutputFormat = 'text' | 'markdown' | 'csv' | 'excel' | 'json'

export type OCREngine = 'tesseract' | 'google_vision'

export interface ExtractionResult {
  documentId: string
  extractedContent: any
  contentType: string
  downloadUrl?: string
  processingTimeMs: number
}
