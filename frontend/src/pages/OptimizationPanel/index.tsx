import React from 'react'
import { OptimizationPanel as OptimizationPanelComponent } from '@/components/OptimizationPanel'

export const OptimizationPanelPage: React.FC = () => {
  return (
    <div className="p-6">
      <OptimizationPanelComponent />
    </div>
  )
}

// 保持向后兼容
export { OptimizationPanelPage as OptimizationPanel }