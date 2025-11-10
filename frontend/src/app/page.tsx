'use client'

import { useState } from 'react'
import { Tab } from '@headlessui/react'
import FillFormTab from '@/components/FillFormTab'
import ExtractTab from '@/components/ExtractTab'
import clsx from 'clsx'

export default function Home() {
  const [selectedIndex, setSelectedIndex] = useState(0)

  return (
    <main className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                PDFSmart Assistant
              </h1>
              <p className="mt-1 text-sm text-gray-600">
                AI-powered PDF form filling and content extraction
              </p>
            </div>
            <div className="flex items-center space-x-4">
              <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
                Free Tier
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <Tab.Group selectedIndex={selectedIndex} onChange={setSelectedIndex}>
          <Tab.List className="flex space-x-1 rounded-xl bg-blue-900/20 p-1 max-w-md mx-auto">
            <Tab
              className={({ selected }) =>
                clsx(
                  'w-full rounded-lg py-2.5 text-sm font-medium leading-5',
                  'ring-white ring-opacity-60 ring-offset-2 ring-offset-blue-400 focus:outline-none focus:ring-2',
                  selected
                    ? 'bg-white text-blue-700 shadow'
                    : 'text-blue-700 hover:bg-white/[0.12] hover:text-blue-800'
                )
              }
            >
              Fill My PDF
            </Tab>
            <Tab
              className={({ selected }) =>
                clsx(
                  'w-full rounded-lg py-2.5 text-sm font-medium leading-5',
                  'ring-white ring-opacity-60 ring-offset-2 ring-offset-blue-400 focus:outline-none focus:ring-2',
                  selected
                    ? 'bg-white text-blue-700 shadow'
                    : 'text-blue-700 hover:bg-white/[0.12] hover:text-blue-800'
                )
              }
            >
              Extract Content
            </Tab>
          </Tab.List>

          <Tab.Panels className="mt-8">
            <Tab.Panel>
              <FillFormTab />
            </Tab.Panel>
            <Tab.Panel>
              <ExtractTab />
            </Tab.Panel>
          </Tab.Panels>
        </Tab.Group>
      </div>

      {/* Footer */}
      <footer className="mt-16 bg-white border-t border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-center text-sm text-gray-600">
            PDFSmart Assistant v1.0.0 - Powered by Docling, Google Gemini, and multiple OCR engines
          </p>
        </div>
      </footer>
    </main>
  )
}
