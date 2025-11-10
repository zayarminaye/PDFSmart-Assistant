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
  fieldName: string
  fieldType: 'text' | 'checkbox' | 'radio' | 'signature' | 'date'
  coordinates: {
    x: number
    y: number
    width: number
    height: number
  }
  pageNumber: number
  currentValue?: string
}

export interface DocumentAnalysis {
  documentId: string
  totalPages: number
  detectedFields: FormField[]
  isScanned: boolean
  ocrEngineUsed?: string
}

export interface ProcessingState {
  isUploading: boolean
  isAnalyzing: boolean
  isProcessing: boolean
  error: string | null
}

export type OutputFormat = 'text' | 'markdown' | 'csv' | 'excel' | 'json'

export interface ExtractionResult {
  documentId: string
  extractedContent: any
  contentType: string
  downloadUrl?: string
  processingTimeMs: number
}
