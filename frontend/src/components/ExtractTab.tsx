'use client'

import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { toast } from 'react-hot-toast'
import { uploadPDF, extractContent, extractTables, extractText } from '@/lib/api'
import { DocumentIcon, CloudArrowUpIcon, MagnifyingGlassIcon } from '@heroicons/react/24/outline'
import type { ProcessingState, OutputFormat, OCREngine } from '@/types'

export default function ExtractTab() {
  const [document, setDocument] = useState<{ id: string; filename: string } | null>(null)
  const [query, setQuery] = useState('')
  const [outputFormat, setOutputFormat] = useState<OutputFormat>('text')
  const [ocrEngine, setOcrEngine] = useState<OCREngine>('tesseract')
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
      const uploadResult = await uploadPDF(file)
      setDocument({
        id: uploadResult.document_id,
        filename: uploadResult.filename,
      })
      toast.success('PDF uploaded successfully!')
      setState(prev => ({ ...prev, isUploading: false }))
    } catch (error: any) {
      console.error('Upload error:', error)
      toast.error(error.response?.data?.detail || 'Upload failed')
      setState(prev => ({ ...prev, isUploading: false, error: error.message }))
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    maxFiles: 1,
  })

  const handleExtract = async () => {
    if (!document || !query.trim()) {
      toast.error('Please provide an extraction query')
      return
    }

    setState(prev => ({ ...prev, isProcessing: true, error: null }))

    try {
      const extractResult = await extractContent(document.id, query, outputFormat, undefined, ocrEngine)
      setResult(extractResult)
      toast.success('Content extracted successfully!')
      setState(prev => ({ ...prev, isProcessing: false }))
    } catch (error: any) {
      console.error('Extraction error:', error)
      toast.error(error.response?.data?.detail || 'Extraction failed')
      setState(prev => ({ ...prev, isProcessing: false, error: error.message }))
    }
  }

  const handleQuickExtract = async (type: 'tables' | 'text') => {
    if (!document) {
      toast.error('Please upload a PDF first')
      return
    }

    setState(prev => ({ ...prev, isProcessing: true, error: null }))

    try {
      let extractResult
      if (type === 'tables') {
        extractResult = await extractTables(document.id)
      } else {
        extractResult = await extractText(document.id)
      }
      setResult({ extracted_content: extractResult, content_type: type })
      toast.success(`${type === 'tables' ? 'Tables' : 'Text'} extracted successfully!`)
      setState(prev => ({ ...prev, isProcessing: false }))
    } catch (error: any) {
      console.error('Quick extraction error:', error)
      toast.error(error.response?.data?.detail || 'Extraction failed')
      setState(prev => ({ ...prev, isProcessing: false, error: error.message }))
    }
  }

  return (
    <div className="space-y-6">
      {/* Upload Area */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Upload PDF Document</h2>

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

        {document && (
          <div className="mt-4 p-4 bg-green-50 rounded-lg">
            <div className="flex items-center">
              <DocumentIcon className="h-5 w-5 text-green-600 mr-2" />
              <div>
                <p className="text-sm font-medium text-green-900">{document.filename}</p>
                <p className="text-xs text-green-700">Ready for extraction</p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Quick Actions */}
      {document && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-3">Quick Actions</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <button
              onClick={() => handleQuickExtract('tables')}
              disabled={state.isProcessing}
              className="px-4 py-3 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
            >
              Extract All Tables
            </button>
            <button
              onClick={() => handleQuickExtract('text')}
              disabled={state.isProcessing}
              className="px-4 py-3 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
            >
              Extract All Text
            </button>
          </div>
        </div>
      )}

      {/* Custom Extraction */}
      {document && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-3">Custom Extraction</h3>
          <p className="text-sm text-gray-600 mb-3">
            Describe what you want to extract. For example:
            "Extract the price list table", "Get all email addresses", "Extract summary section"
          </p>

          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="What do you want to extract?"
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            rows={3}
          />

          <div className="mt-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Output Format
            </label>
            <select
              value={outputFormat}
              onChange={(e) => setOutputFormat(e.target.value as OutputFormat)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="text">Plain Text</option>
              <option value="markdown">Markdown</option>
              <option value="json">JSON</option>
              <option value="csv">CSV</option>
            </select>
          </div>

          <div className="mt-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              OCR Engine
            </label>
            <select
              value={ocrEngine}
              onChange={(e) => setOcrEngine(e.target.value as OCREngine)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="tesseract">Tesseract (Free, Fast)</option>
              <option value="google_vision">Google Vision (Best Quality, 1000 free/month)</option>
            </select>
            <p className="mt-1 text-xs text-gray-500">
              Choose OCR engine for scanned documents
            </p>
          </div>

          <button
            onClick={handleExtract}
            disabled={state.isProcessing || !query.trim()}
            className="mt-4 w-full inline-flex items-center justify-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {state.isProcessing ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                Extracting...
              </>
            ) : (
              <>
                <MagnifyingGlassIcon className="h-5 w-5 mr-2" />
                Extract with AI
              </>
            )}
          </button>
        </div>
      )}

      {/* Result */}
      {result && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-3">Extracted Content</h3>

          <div className="bg-gray-50 rounded-lg p-4 max-h-96 overflow-y-auto">
            <pre className="text-sm text-gray-800 whitespace-pre-wrap font-mono">
              {typeof result.extracted_content === 'string'
                ? result.extracted_content
                : JSON.stringify(result.extracted_content, null, 2)}
            </pre>
          </div>

          {result.processing_time_ms && (
            <p className="text-xs text-gray-500 mt-2">
              Processing time: {result.processing_time_ms}ms
            </p>
          )}

          <div className="mt-4 flex space-x-3">
            <button
              onClick={() => {
                const content = typeof result.extracted_content === 'string'
                  ? result.extracted_content
                  : JSON.stringify(result.extracted_content, null, 2)
                navigator.clipboard.writeText(content)
                toast.success('Copied to clipboard!')
              }}
              className="flex-1 px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
            >
              Copy to Clipboard
            </button>
            <button className="flex-1 px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50">
              Download
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
