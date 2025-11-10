'use client'

import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { toast } from 'react-hot-toast'
import { uploadPDF, analyzePDF, fillForm } from '@/lib/api'
import { DocumentIcon, CloudArrowUpIcon, SparklesIcon } from '@heroicons/react/24/outline'
import type { DocumentAnalysis, ProcessingState } from '@/types'

export default function FillFormTab() {
  const [document, setDocument] = useState<{ id: string; filename: string } | null>(null)
  const [analysis, setAnalysis] = useState<DocumentAnalysis | null>(null)
  const [instructions, setInstructions] = useState('')
  const [result, setResult] = useState<any>(null)
  const [state, setState] = useState<ProcessingState>({
    isUploading: false,
    isAnalyzing: false,
    isProcessing: false,
    error: null,
  })

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0]
    if (!file) return

    if (!file.name.endsWith('.pdf')) {
      toast.error('Please upload a PDF file')
      return
    }

    setState(prev => ({ ...prev, isUploading: true, error: null }))

    try {
      // Upload PDF
      const uploadResult = await uploadPDF(file)
      setDocument({
        id: uploadResult.document_id,
        filename: uploadResult.filename,
      })
      toast.success('PDF uploaded successfully!')

      // Auto-analyze
      setState(prev => ({ ...prev, isUploading: false, isAnalyzing: true }))
      const analysisResult = await analyzePDF(uploadResult.document_id)
      setAnalysis(analysisResult)

      if (analysisResult.detected_fields.length === 0) {
        toast.error('No form fields detected in this PDF')
      } else {
        toast.success(`Detected ${analysisResult.detected_fields.length} form fields`)
      }

      setState(prev => ({ ...prev, isAnalyzing: false }))
    } catch (error: any) {
      console.error('Upload/Analysis error:', error)
      toast.error(error.response?.data?.detail || 'Upload failed')
      setState(prev => ({ ...prev, isUploading: false, isAnalyzing: false, error: error.message }))
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    maxFiles: 1,
  })

  const handleFillForm = async () => {
    if (!document || !instructions.trim()) {
      toast.error('Please provide filling instructions')
      return
    }

    setState(prev => ({ ...prev, isProcessing: true, error: null }))

    try {
      const fillResult = await fillForm(document.id, instructions)
      setResult(fillResult)
      toast.success(`Filled ${fillResult.fields_filled}/${fillResult.fields_total} fields!`)
      setState(prev => ({ ...prev, isProcessing: false }))
    } catch (error: any) {
      console.error('Fill form error:', error)
      toast.error(error.response?.data?.detail || 'Form filling failed')
      setState(prev => ({ ...prev, isProcessing: false, error: error.message }))
    }
  }

  return (
    <div className="space-y-6">
      {/* Upload Area */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Upload PDF Form</h2>

        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors ${
            isDragActive
              ? 'border-blue-500 bg-blue-50'
              : 'border-gray-300 hover:border-blue-400'
          }`}
        >
          <input {...getInputProps()} />
          <CloudArrowUpIcon className="mx-auto h-12 w-12 text-gray-400" />
          <p className="mt-2 text-sm text-gray-600">
            {isDragActive ? 'Drop the PDF here' : 'Drag & drop a PDF, or click to select'}
          </p>
          <p className="mt-1 text-xs text-gray-500">PDF files only, max 10MB</p>
        </div>

        {state.isUploading && (
          <div className="mt-4 text-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <p className="mt-2 text-sm text-gray-600">Uploading...</p>
          </div>
        )}

        {state.isAnalyzing && (
          <div className="mt-4 text-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <p className="mt-2 text-sm text-gray-600">Analyzing PDF...</p>
          </div>
        )}

        {document && analysis && (
          <div className="mt-4 p-4 bg-green-50 rounded-lg">
            <div className="flex items-center">
              <DocumentIcon className="h-5 w-5 text-green-600 mr-2" />
              <div>
                <p className="text-sm font-medium text-green-900">{document.filename}</p>
                <p className="text-xs text-green-700">
                  {analysis.total_pages} pages • {analysis.detected_fields.length} fields detected
                  {analysis.is_scanned && ' • Scanned document'}
                </p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Form Fields Info */}
      {analysis && analysis.detected_fields.length > 0 && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-3">Detected Form Fields</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {analysis.detected_fields.slice(0, 10).map((field, idx) => (
              <div key={idx} className="text-sm p-2 bg-gray-50 rounded">
                <span className="font-medium">{field.field_name || `Field ${idx + 1}`}</span>
                <span className="text-gray-500 ml-2">({field.field_type})</span>
              </div>
            ))}
          </div>
          {analysis.detected_fields.length > 10 && (
            <p className="mt-2 text-xs text-gray-500">
              ...and {analysis.detected_fields.length - 10} more fields
            </p>
          )}
        </div>
      )}

      {/* Instructions */}
      {document && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-3">Fill Instructions</h3>
          <p className="text-sm text-gray-600 mb-3">
            Describe how to fill the form in natural language. For example:
            "Fill name as John Doe, address as 123 Main St, and today's date"
          </p>

          <textarea
            value={instructions}
            onChange={(e) => setInstructions(e.target.value)}
            placeholder="Enter filling instructions..."
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            rows={4}
          />

          <button
            onClick={handleFillForm}
            disabled={state.isProcessing || !instructions.trim()}
            className="mt-4 w-full inline-flex items-center justify-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {state.isProcessing ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                Processing...
              </>
            ) : (
              <>
                <SparklesIcon className="h-5 w-5 mr-2" />
                Fill Form with AI
              </>
            )}
          </button>
        </div>
      )}

      {/* Result */}
      {result && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-3">Result</h3>
          <div className="p-4 bg-green-50 rounded-lg">
            <p className="text-sm text-green-900">
              Successfully filled {result.fields_filled} out of {result.fields_total} fields
            </p>
            <p className="text-xs text-green-700 mt-1">
              Processing time: {result.processing_time_ms}ms
            </p>
          </div>

          <button className="mt-4 w-full px-6 py-3 border border-gray-300 text-base font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50">
            Download Filled PDF
          </button>
        </div>
      )}
    </div>
  )
}
