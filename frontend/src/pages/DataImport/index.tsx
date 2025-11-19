import React from 'react'
import { DataImport } from '@/components/DataImport'

export const DataImportPage: React.FC = () => {
  return (
    <div className="p-6">
      <DataImport />
    </div>
  )
}

// 保持向后兼容
export { DataImportPage as DataImport }