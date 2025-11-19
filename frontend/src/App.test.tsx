import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { Layout, Card, Button, Typography } from 'antd'

const { Content } = Layout
const { Title, Text } = Typography

// 简单的测试组件
const TestDashboard: React.FC = () => {
  return (
    <div className="p-6">
      <Title level={2}>测试仪表板</Title>
      <Card>
        <Text>如果您能看到这个页面，说明React应用正在正常运行！</Text>
        <div style={{ marginTop: 16 }}>
          <Button type="primary">测试按钮</Button>
        </div>
      </Card>
    </div>
  )
}

function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Layout className="min-h-screen">
        <Content className="p-6">
          <Routes>
            {/* 默认重定向到测试仪表板 */}
            <Route path="/" element={<Navigate to="/dashboard" replace />} />

            {/* 测试页面路由 */}
            <Route path="/dashboard" element={<TestDashboard />} />

            {/* 404页面 */}
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </Content>
      </Layout>
    </div>
  )
}

export default App