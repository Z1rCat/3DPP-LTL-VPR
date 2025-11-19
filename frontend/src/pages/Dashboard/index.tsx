import React, { useState, useEffect } from 'react'
import { Row, Col, Card, Statistic, Progress, Table, Tag, Button, Space, Typography, Alert } from 'antd'
import { useNavigate } from 'react-router-dom'
import {
  CarOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  TrophyOutlined,
  ReloadOutlined,
  RightOutlined,
  BarChartOutlined,
  UploadOutlined,
  SettingOutlined
} from '@ant-design/icons'
import { motion } from 'framer-motion'

const { Title, Text } = Typography

export const Dashboard: React.FC = () => {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [stats, setStats] = useState({
    totalVehicles: 12,
    activeVehicles: 8,
    totalOrders: 156,
    completedOrders: 142,
    averageEfficiency: 89.5,
    totalDistance: 2847.5,
  })

  // 模拟数据
  const recentVehicles = [
    {
      id: 'LARGE_TRUCK_000',
      name: '大型货车001',
      status: 'active',
      efficiency: 94.5,
      route: '成都→重庆→贵阳',
      nextStop: '重庆配送中心',
    },
    {
      id: 'MEDIUM_TRUCK_001',
      name: '中型货车002',
      status: 'completed',
      efficiency: 88.2,
      route: '成都→绵阳→德阳',
      nextStop: '任务完成',
    },
    {
      id: 'LTL_TRUCK_000',
      name: '零担货车001',
      status: 'loading',
      efficiency: 92.1,
      route: '成都→内江→自贡',
      nextStop: '装载中...',
    },
  ]

  const columns = [
    {
      title: '车辆编号',
      dataIndex: 'id',
      key: 'id',
      render: (text: string) => (
        <Text strong className="text-primary-600">{text}</Text>
      ),
    },
    {
      title: '车辆名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const statusConfig = {
          active: { color: 'green', text: '运输中' },
          completed: { color: 'blue', text: '已完成' },
          loading: { color: 'orange', text: '装载中' },
          pending: { color: 'gray', text: '待分配' },
        }
        const config = statusConfig[status as keyof typeof statusConfig]
        return <Tag color={config?.color}>{config?.text}</Tag>
      },
    },
    {
      title: '效率评分',
      dataIndex: 'efficiency',
      key: 'efficiency',
      render: (efficiency: number) => (
        <div className="flex items-center space-x-2">
          <Progress
            percent={efficiency}
            size="small"
            showInfo={false}
            strokeColor={
              efficiency >= 90 ? '#52c41a' : efficiency >= 80 ? '#faad14' : '#f5222d'
            }
            className="w-20"
          />
          <Text className="text-sm font-medium">{efficiency}%</Text>
        </div>
      ),
    },
    {
      title: '当前路线',
      dataIndex: 'route',
      key: 'route',
    },
    {
      title: '下一站',
      dataIndex: 'nextStop',
      key: 'nextStop',
      render: (nextStop: string) => (
        <Text className="text-gray-600">{nextStop}</Text>
      ),
    },
  ]

  const quickActions = [
    {
      title: '数据导入',
      description: '导入订单和车辆数据',
      icon: <UploadOutlined className="text-2xl" />,
      color: 'bg-blue-50 text-blue-600 border-blue-200',
      action: () => navigate('/import'),
    },
    {
      title: '开始优化',
      description: '执行智能路径优化',
      icon: <BarChartOutlined className="text-2xl" />,
      color: 'bg-green-50 text-green-600 border-green-200',
      action: () => navigate('/optimization'),
    },
    {
      title: '车辆管理',
      description: '查看和管理车辆状态',
      icon: <CarOutlined className="text-2xl" />,
      color: 'bg-orange-50 text-orange-600 border-orange-200',
      action: () => navigate('/vehicles'),
    },
    {
      title: '可视化分析',
      description: '查看优化结果可视化',
      icon: <TrophyOutlined className="text-2xl" />,
      color: 'bg-purple-50 text-purple-600 border-purple-200',
      action: () => navigate('/visualization'),
    },
  ]

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
      },
    },
  }

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1,
    },
  }

  return (
    <motion.div
      className="p-6 lg:p-8"
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      {/* 页面标题 */}
      <div className="mb-8">
        <Title level={2} className="mb-2">
          智能物流优化控制台
        </Title>
        <Text className="text-gray-600">
          实时监控车辆状态，优化配送效率，提升物流管理水平
        </Text>
      </div>

      {/* 系统状态提示 */}
      <Alert
        message="系统运行正常"
        description="所有优化算法运行正常，3D装箱和路径规划功能可用"
        type="success"
        showIcon
        closable
        className="mb-6"
      />

      {/* 统计卡片 */}
      <Row gutter={[24, 24]} className="mb-8">
        <Col xs={24} sm={12} lg={6}>
          <motion.div variants={itemVariants}>
            <Card className="h-full card">
              <Statistic
                title="车辆总数"
                value={stats.totalVehicles}
                prefix={<CarOutlined className="text-primary-500" />}
                valueStyle={{ color: '#1890ff' }}
              />
              <div className="mt-2">
                <Text type="secondary">
                  活跃车辆: {stats.activeVehicles}
                </Text>
              </div>
            </Card>
          </motion.div>
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <motion.div variants={itemVariants}>
            <Card className="h-full card">
              <Statistic
                title="订单完成率"
                value={Math.round((stats.completedOrders / stats.totalOrders) * 100)}
                suffix="%"
                prefix={<CheckCircleOutlined className="text-success-500" />}
                valueStyle={{ color: '#52c41a' }}
              />
              <div className="mt-2">
                <Text type="secondary">
                  已完成: {stats.completedOrders} / {stats.totalOrders}
                </Text>
              </div>
            </Card>
          </motion.div>
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <motion.div variants={itemVariants}>
            <Card className="h-full card">
              <Statistic
                title="平均效率"
                value={stats.averageEfficiency}
                suffix="%"
                prefix={<TrophyOutlined className="text-warning-500" />}
                valueStyle={{ color: '#faad14' }}
              />
              <div className="mt-2">
                <Progress
                  percent={stats.averageEfficiency}
                  size="small"
                  strokeColor={{
                    '0%': '#f5222d',
                    '50%': '#faad14',
                    '100%': '#52c41a',
                  }}
                />
              </div>
            </Card>
          </motion.div>
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <motion.div variants={itemVariants}>
            <Card className="h-full card">
              <Statistic
                title="总配送里程"
                value={stats.totalDistance}
                suffix="km"
                prefix={<ClockCircleOutlined className="text-info-500" />}
                valueStyle={{ color: '#722ed1' }}
              />
              <div className="mt-2">
                <Text type="secondary">本月累计</Text>
              </div>
            </Card>
          </motion.div>
        </Col>
      </Row>

      {/* 快捷操作 */}
      <motion.div variants={itemVariants} className="mb-8">
        <Card title="快捷操作" className="card">
          <Row gutter={[16, 16]}>
            {quickActions.map((action, index) => (
              <Col xs={24} sm={12} lg={6} key={index}>
                <div
                  className={`p-4 border rounded-lg cursor-pointer transition-all duration-200 hover:shadow-md hover:-translate-y-1 ${action.color}`}
                  onClick={action.action}
                >
                  <div className="flex items-start space-x-3">
                    <div>{action.icon}</div>
                    <div className="flex-1">
                      <div className="font-medium mb-1">{action.title}</div>
                      <Text className="text-sm opacity-75">{action.description}</Text>
                    </div>
                    <RightOutlined className="text-sm opacity-50" />
                  </div>
                </div>
              </Col>
            ))}
          </Row>
        </Card>
      </motion.div>

      {/* 最近车辆状态 */}
      <motion.div variants={itemVariants}>
        <Card
          title="最近车辆状态"
          extra={
            <Button
              type="text"
              icon={<ReloadOutlined />}
              onClick={() => setLoading(true)}
              loading={loading}
            >
              刷新
            </Button>
          }
          className="card"
        >
          <Table
            dataSource={recentVehicles}
            columns={columns}
            rowKey="id"
            pagination={false}
            size="middle"
            loading={loading}
          />
        </Card>
      </motion.div>
    </motion.div>
  )
}