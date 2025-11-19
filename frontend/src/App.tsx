import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { Layout, Card, Button, Typography, Menu, Space } from 'antd'
import { useNavigate } from 'react-router-dom'
import {
  DashboardOutlined,
  UploadOutlined,
  BarChartOutlined,
  CarOutlined,
  EyeOutlined
} from '@ant-design/icons'

const { Content, Sider, Header } = Layout
const { Title, Text } = Typography

// 仪表板组件
const SimpleDashboard: React.FC = () => {
  return (
    <div className="p-6">
      <Title level={2}>🚚 智能物流优化控制台</Title>
      <div style={{ marginBottom: 24 }}>
        <Text type="secondary">实时监控车辆状态，优化配送效率，提升物流管理水平</Text>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 16, marginBottom: 24 }}>
        <Card>
          <Title level={4}>🚛 车辆总数</Title>
          <div style={{ fontSize: 32, color: '#1890ff', fontWeight: 'bold' }}>12</div>
          <Text type="secondary">活跃车辆: 8</Text>
        </Card>

        <Card>
          <Title level={4}>📦 订单完成率</Title>
          <div style={{ fontSize: 32, color: '#52c41a', fontWeight: 'bold' }}>91%</div>
          <Text type="secondary">已完成: 142 / 156</Text>
        </Card>

        <Card>
          <Title level={4}>⚡ 平均效率</Title>
          <div style={{ fontSize: 32, color: '#faad14', fontWeight: 'bold' }}>89.5%</div>
          <Text type="secondary">系统运行良好</Text>
        </Card>
      </div>

      <Card title="系统状态" style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', alignItems: 'center', color: '#52c41a' }}>
          <span style={{ marginRight: 8 }}>●</span>
          系统运行正常 - 所有优化算法运行正常，3D装箱和路径规划功能可用
        </div>
      </Card>

      <Card title="快捷操作">
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16 }}>
          <Button type="primary" size="large" icon={<UploadOutlined />} block>
            数据导入
          </Button>
          <Button size="large" icon={<BarChartOutlined />} block>
            开始优化
          </Button>
          <Button size="large" icon={<CarOutlined />} block>
            车辆管理
          </Button>
          <Button size="large" icon={<EyeOutlined />} block>
            可视化
          </Button>
        </div>
      </Card>
    </div>
  )
}

// 数据导入组件
const DataImportPage: React.FC = () => {
  return (
    <div className="p-6">
      <Title level={2}>📤 数据导入</Title>
      <div style={{ marginBottom: 24 }}>
        <Text type="secondary">导入订单、车辆和客户数据，支持多种文件格式</Text>
      </div>

      <Card title="文件上传区域" style={{ marginBottom: 24 }}>
        <div style={{
          border: '2px dashed #d9d9d9',
          borderRadius: 8,
          padding: 60,
          textAlign: 'center',
          background: '#fafafa'
        }}>
          <UploadOutlined style={{ fontSize: 48, color: '#1890ff', marginBottom: 16 }} />
          <div style={{ fontSize: 16, marginBottom: 8 }}>拖拽文件到这里，或点击上传</div>
          <Text type="secondary">支持 CSV、JSON、Excel 格式，可同时上传多个文件</Text>
          <div style={{ marginTop: 16 }}>
            <Button type="primary" icon={<UploadOutlined />}>选择文件</Button>
          </div>
        </div>
      </Card>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
        <Card title="数据模板">
          <div style={{ marginBottom: 16 }}>
            <Text>建议使用标准模板，确保数据格式正确</Text>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            <Button icon={<UploadOutlined />} style={{ textAlign: 'left' }}>
              车辆数据模板 (CSV)
            </Button>
            <Button icon={<UploadOutlined />} style={{ textAlign: 'left' }}>
              订单数据模板 (CSV)
            </Button>
            <Button icon={<UploadOutlined />} style={{ textAlign: 'left' }}>
              客户数据模板 (CSV)
            </Button>
          </div>
        </Card>

        <Card title="导入历史">
          <Text type="secondary">暂无导入历史记录</Text>
        </Card>
      </div>
    </div>
  )
}

// 优化执行组件
const OptimizationPage: React.FC = () => {
  const [isOptimizing, setIsOptimizing] = React.useState(false)
  const [progress, setProgress] = React.useState(0)

  const startOptimization = () => {
    setIsOptimizing(true)
    setProgress(0)
    const interval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 100) {
          setIsOptimizing(false)
          clearInterval(interval)
          return 100
        }
        return prev + 10
      })
    }, 500)
  }

  return (
    <div className="p-6">
      <Title level={2}>⚙️ 优化执行</Title>
      <div style={{ marginBottom: 24 }}>
        <Text type="secondary">启动智能物流优化算法，执行3D装箱和路径规划</Text>
      </div>

      <Card title="优化控制面板" style={{ marginBottom: 24 }}>
        <div style={{ marginBottom: 24 }}>
          <Title level={4}>智能物流优化引擎</Title>
          <Text type="secondary">基于3D装箱与路径规划的混合优化算法</Text>
        </div>

        <div style={{ marginBottom: 24 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Space size="large">
              <Button
                type="primary"
                size="large"
                icon={<BarChartOutlined />}
                onClick={startOptimization}
                disabled={isOptimizing}
              >
                {isOptimizing ? '优化中...' : '开始优化'}
              </Button>
              {isOptimizing && (
                <Button size="large" onClick={() => setIsOptimizing(false)}>
                  停止优化
                </Button>
              )}
            </Space>
            {isOptimizing && (
              <Text type="secondary">预计剩余时间: 2分30秒</Text>
            )}
          </div>
        </div>

        {isOptimizing && (
          <div style={{ marginBottom: 24 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
              <Text strong>优化进度</Text>
              <Text strong>{progress}%</Text>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              <div>
                <Text>数据预处理</Text>
                <div style={{ background: '#f0f0f0', height: 4, borderRadius: 2, overflow: 'hidden' }}>
                  <div style={{
                    background: '#52c41a',
                    height: '100%',
                    width: progress > 30 ? '100%' : `${progress * 3.33}%`,
                    transition: 'width 0.3s ease'
                  }} />
                </div>
              </div>
              <div>
                <Text>3D装箱计算</Text>
                <div style={{ background: '#f0f0f0', height: 4, borderRadius: 2, overflow: 'hidden' }}>
                  <div style={{
                    background: '#1890ff',
                    height: '100%',
                    width: progress > 60 ? '100%' : progress > 30 ? `${(progress - 30) * 3.33}%` : '0%',
                    transition: 'width 0.3s ease'
                  }} />
                </div>
              </div>
              <div>
                <Text>路径规划优化</Text>
                <div style={{ background: '#f0f0f0', height: 4, borderRadius: 2, overflow: 'hidden' }}>
                  <div style={{
                    background: '#faad14',
                    height: '100%',
                    width: progress > 90 ? '100%' : progress > 60 ? `${(progress - 60) * 3.33}%` : '0%',
                    transition: 'width 0.3s ease'
                  }} />
                </div>
              </div>
            </div>
          </div>
        )}

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16 }}>
          <Card size="small">
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 24, color: '#1890ff' }}>12</div>
              <Text type="secondary">车辆数量</Text>
            </div>
          </Card>
          <Card size="small">
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 24, color: '#52c41a' }}>156</div>
              <Text type="secondary">订单数量</Text>
            </div>
          </Card>
          <Card size="small">
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 24, color: '#faad14' }}>5分钟</div>
              <Text type="secondary">预计时间</Text>
            </div>
          </Card>
        </div>
      </Card>

      <Card title="优化参数">
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 16 }}>
          <div>
            <Text strong>优化目标:</Text>
            <div style={{ marginTop: 8 }}>
              <div>最短距离 (40%)</div>
              <div>最短时间 (30%)</div>
              <div>最高利用率 (30%)</div>
            </div>
          </div>
          <div>
            <Text strong>约束条件:</Text>
            <div style={{ marginTop: 8 }}>
              <div>✓ 时间窗口限制</div>
              <div>✓ 车辆容量限制</div>
              <div>✓ 司机工作时间</div>
            </div>
          </div>
        </div>
      </Card>
    </div>
  )
}

// 车辆管理组件
const VehicleManagementPage: React.FC = () => {
  const vehicles = [
    { id: 'LARGE_TRUCK_000', name: '大型货车001', status: '运输中', efficiency: 94.5, route: '成都→重庆→贵阳' },
    { id: 'MEDIUM_TRUCK_001', name: '中型货车002', status: '已完成', efficiency: 88.2, route: '成都→绵阳→德阳' },
    { id: 'LTL_TRUCK_000', name: '零担货车001', status: '装载中', efficiency: 92.1, route: '成都→内江→自贡' },
  ]

  return (
    <div className="p-6">
      <Title level={2}>🚛 车辆管理</Title>
      <div style={{ marginBottom: 24 }}>
        <Text type="secondary">监控车辆状态，管理车辆信息和配送任务</Text>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 16, marginBottom: 24 }}>
        <Card>
          <Title level={4}>🚛 车辆总数</Title>
          <div style={{ fontSize: 32, color: '#1890ff', fontWeight: 'bold' }}>12</div>
          <Text type="secondary">正常运营</Text>
        </Card>
        <Card>
          <Title level={4}>🚚 运输中</Title>
          <div style={{ fontSize: 32, color: '#52c41a', fontWeight: 'bold' }}>8</div>
          <Text type="secondary">正在执行任务</Text>
        </Card>
        <Card>
          <Title level={4}>🏭 待分配</Title>
          <div style={{ fontSize: 32, color: '#faad14', fontWeight: 'bold' }}>4</div>
          <Text type="secondary">等待任务分配</Text>
        </Card>
      </div>

      <Card title="车辆列表">
        <div style={{ display: 'grid', gap: 16 }}>
          {vehicles.map(vehicle => (
            <Card key={vehicle.id} size="small" style={{ background: '#fafafa' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ fontWeight: 'bold', color: '#1890ff' }}>{vehicle.id}</div>
                  <div>{vehicle.name}</div>
                  <div style={{ fontSize: 12, color: '#8c8c8c' }}>{vehicle.route}</div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{
                    padding: '4px 8px',
                    borderRadius: 4,
                    background: vehicle.status === '运输中' ? '#f6ffed' :
                               vehicle.status === '已完成' ? '#e6f7ff' : '#fffbe6',
                    color: vehicle.status === '运输中' ? '#52c41a' :
                            vehicle.status === '已完成' ? '#1890ff' : '#faad14',
                    fontSize: 12,
                    marginBottom: 8
                  }}>
                    {vehicle.status}
                  </div>
                  <div style={{ fontWeight: 'bold' }}>{vehicle.efficiency}%</div>
                  <div style={{ fontSize: 12, color: '#8c8c8c' }}>效率</div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </Card>
    </div>
  )
}

function App() {
  const navigate = useNavigate()

  const menuItems = [
    {
      key: 'dashboard',
      icon: <DashboardOutlined />,
      label: '仪表板',
    },
    {
      key: 'import',
      icon: <UploadOutlined />,
      label: '数据导入',
    },
    {
      key: 'optimization',
      icon: <BarChartOutlined />,
      label: '优化执行',
    },
    {
      key: 'vehicles',
      icon: <CarOutlined />,
      label: '车辆管理',
    },
  ]

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider width={240} style={{ background: '#fff', borderRight: '1px solid #f0f0f0' }}>
        <div style={{ padding: 16, borderBottom: '1px solid #f0f0f0' }}>
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <div style={{
              width: 32,
              height: 32,
              background: 'linear-gradient(135deg, #1890ff, #40a9ff)',
              borderRadius: 8,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'white',
              fontWeight: 'bold',
              marginRight: 12
            }}>
              巧
            </div>
            <div>
              <div style={{ fontWeight: 'bold', fontSize: 14 }}>巧满装载</div>
              <div style={{ fontSize: 12, color: '#8c8c8c' }}>智能物流优化</div>
            </div>
          </div>
        </div>

        <Menu
          mode="inline"
          selectedKeys={['dashboard']}
          items={menuItems}
          onClick={({ key }) => navigate(`/${key}`)}
        />
      </Sider>

      <Layout>
        <Header style={{
          background: '#fff',
          padding: '0 24px',
          borderBottom: '1px solid #f0f0f0',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <Title level={4} style={{ margin: 0, color: '#1890ff' }}>
            企业级智能物流优化系统
          </Title>
          <Space>
            <span style={{ color: '#8c8c8c' }}>管理员</span>
          </Space>
        </Header>

        <Content style={{ margin: 0, background: '#f0f2f5' }}>
          <Routes>
            {/* 默认重定向到仪表板 */}
            <Route path="/" element={<Navigate to="/dashboard" replace />} />

            {/* 主要页面路由 */}
            <Route path="/dashboard" element={<SimpleDashboard />} />
            <Route path="/import" element={<DataImportPage />} />
            <Route path="/optimization" element={<OptimizationPage />} />
            <Route path="/vehicles" element={<VehicleManagementPage />} />

            {/* 404页面 */}
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </Content>
      </Layout>
    </Layout>
  )
}

export default App