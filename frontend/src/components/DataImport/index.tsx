import React, { useState, useCallback } from 'react'
import { Card, Upload, Button, message, Progress, Table, Tag, Space, Typography, Alert, Tabs, Modal } from 'antd'
import { motion, AnimatePresence } from 'framer-motion'
import {
  InboxOutlined,
  UploadOutlined,
  DownloadOutlined,
  EyeOutlined,
  DeleteOutlined,
  FileTextOutlined,
  FileExcelOutlined,
  FileUnknownOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  LoadingOutlined
} from '@ant-design/icons'
import { useDropzone } from 'react-beautiful-dnd'
import type { UploadProps } from 'antd'
import type { ImportTask, ImportError } from '@/types'

const { Dragger } = Upload
const { Title, Text, Paragraph } = Typography
const { TabPane } = Tabs

export interface DataImportProps {
  onImportComplete?: (task: ImportTask) => void
  onError?: (error: string) => void
}

interface FileItem {
  id: string
  file: File
  status: 'pending' | 'uploading' | 'validating' | 'processing' | 'completed' | 'error'
  progress: number
  errors?: ImportError[]
  preview?: any[]
}

export const DataImport: React.FC<DataImportProps> = ({ onImportComplete, onError }) => {
  const [files, setFiles] = useState<FileItem[]>([])
  const [isModalVisible, setIsModalVisible] = useState(false)
  const [previewFile, setPreviewFile] = useState<FileItem | null>(null)
  const [importHistory, setImportHistory] = useState<ImportTask[]>([])

  // 文件类型配置
  const fileTypes = [
    { type: 'csv', label: 'CSV文件', icon: <FileTextOutlined />, accept: '.csv' },
    { type: 'json', label: 'JSON文件', icon: <FileTextOutlined />, accept: '.json' },
    { type: 'excel', label: 'Excel文件', icon: <FileExcelOutlined />, accept: '.xlsx,.xls' },
  ]

  // 模板文件配置
  const templates = [
    { name: '车辆数据模板', type: 'vehicles', url: '/templates/vehicles_template.csv' },
    { name: '订单数据模板', type: 'orders', url: '/templates/orders_template.csv' },
    { name: '客户数据模板', type: 'customers', url: '/templates/customers_template.csv' },
  ]

  // 处理文件选择
  const handleFileSelect = useCallback((selectedFiles: File[]) => {
    const newFiles: FileItem[] = selectedFiles.map(file => ({
      id: Math.random().toString(36).substr(2, 9),
      file,
      status: 'pending',
      progress: 0,
    }))

    setFiles(prev => [...prev, ...newFiles])

    // 自动开始上传
    newFiles.forEach(fileItem => {
      processFile(fileItem)
    })
  }, [])

  // 拖拽上传配置
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: handleFileSelect,
    accept: {
      'text/csv': ['.csv'],
      'application/json': ['.json'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
    },
    multiple: true,
  })

  // 处理文件上传和验证
  const processFile = async (fileItem: FileItem) => {
    try {
      // 更新状态为上传中
      updateFileStatus(fileItem.id, 'uploading', 0)

      // 模拟文件上传
      await simulateProgress(fileItem.id, 0, 30, 1000)

      // 更新状态为验证中
      updateFileStatus(fileItem.id, 'validating', 30)

      // 模拟文件验证
      await simulateProgress(fileItem.id, 30, 60, 1500)

      // 验证文件格式和内容
      const validation = await validateFile(fileItem.file)
      if (!validation.valid && validation.errors) {
        updateFileStatus(fileItem.id, 'error', 60, validation.errors)
        return
      }

      // 更新状态为处理中
      updateFileStatus(fileItem.id, 'processing', 60)

      // 模拟数据处理
      await simulateProgress(fileItem.id, 60, 100, 2000)

      // 完成处理
      updateFileStatus(fileItem.id, 'completed', 100, undefined, validation.preview)

    } catch (error) {
      updateFileStatus(fileItem.id, 'error', 0, [{ row: 0, field: 'file', value: '', message: '处理失败', severity: 'error' }])
    }
  }

  // 模拟进度更新
  const simulateProgress = (fileId: string, from: number, to: number, duration: number): Promise<void> => {
    return new Promise((resolve) => {
      const steps = 20
      const stepDuration = duration / steps
      const stepSize = (to - from) / steps
      let currentStep = 0

      const interval = setInterval(() => {
        currentStep++
        const progress = from + (stepSize * currentStep)

        if (currentStep >= steps) {
          updateFileStatus(fileId, files.find(f => f.id === fileId)?.status || 'pending', to)
          clearInterval(interval)
          resolve()
        } else {
          updateFileStatus(fileId, files.find(f => f.id === fileId)?.status || 'pending', progress)
        }
      }, stepDuration)
    })
  }

  // 验证文件
  const validateFile = async (file: File): Promise<{ valid: boolean; errors?: ImportError[]; preview?: any[] }> => {
    // 模拟文件验证逻辑
    const fileExtension = file.name.split('.').pop()?.toLowerCase()

    if (!['csv', 'json', 'xlsx', 'xls'].includes(fileExtension || '')) {
      return {
        valid: false,
        errors: [{ row: 1, field: 'format', value: fileExtension, message: '不支持的文件格式', severity: 'error' }]
      }
    }

    // 模拟成功验证和预览数据
    const preview = [
      { id: '001', name: '测试数据1', type: 'vehicle', status: 'active' },
      { id: '002', name: '测试数据2', type: 'vehicle', status: 'inactive' },
    ]

    return { valid: true, preview }
  }

  // 更新文件状态
  const updateFileStatus = (fileId: string, status: FileItem['status'], progress: number, errors?: ImportError[], preview?: any[]) => {
    setFiles(prev => prev.map(file =>
      file.id === fileId
        ? { ...file, status, progress, errors, preview }
        : file
    ))
  }

  // 删除文件
  const removeFile = (fileId: string) => {
    setFiles(prev => prev.filter(file => file.id !== fileId))
  }

  // 预览文件内容
  const previewFileContent = (file: FileItem) => {
    setPreviewFile(file)
    setIsModalVisible(true)
  }

  // 下载模板
  const downloadTemplate = (template: typeof templates[0]) => {
    // 模拟下载模板
    message.info(`正在下载 ${template.name}...`)
  }

  // 获取文件图标
  const getFileIcon = (fileName: string) => {
    const extension = fileName.split('.').pop()?.toLowerCase()
    switch (extension) {
      case 'csv':
      case 'json':
        return <FileTextOutlined className="text-blue-500" />
      case 'xlsx':
      case 'xls':
        return <FileExcelOutlined className="text-green-500" />
      default:
        return <FileUnknownOutlined className="text-gray-500" />
    }
  }

  // 获取状态图标
  const getStatusIcon = (status: FileItem['status']) => {
    switch (status) {
      case 'uploading':
      case 'validating':
      case 'processing':
        return <LoadingOutlined className="text-blue-500" spin />
      case 'completed':
        return <CheckCircleOutlined className="text-green-500" />
      case 'error':
        return <CloseCircleOutlined className="text-red-500" />
      default:
        return <LoadingOutlined />
    }
  }

  const previewColumns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
    },
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => (
        <Tag color={type === 'vehicle' ? 'blue' : 'green'}>
          {type === 'vehicle' ? '车辆' : '其他'}
        </Tag>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={status === 'active' ? 'green' : 'orange'}>
          {status === 'active' ? '活跃' : '非活跃'}
        </Tag>
      ),
    },
  ]

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="space-y-6"
    >
      <Title level={2}>数据导入</Title>

      {/* 文件上传区域 */}
      <Card>
        <div
          {...getRootProps()}
          className={`p-8 border-2 border-dashed rounded-lg cursor-pointer transition-all duration-200 ${
            isDragActive
              ? 'border-primary-500 bg-primary-50'
              : 'border-gray-300 hover:border-primary-300 hover:bg-gray-50'
          }`}
        >
          <input {...getInputProps()} />
          <div className="text-center">
            <InboxOutlined className="text-4xl text-gray-400 mb-4" />
            <Title level={4} className="mb-2">
              {isDragActive ? '释放文件到这里' : '拖拽文件到这里，或点击选择文件'}
            </Title>
            <Text type="secondary">
              支持 CSV、JSON、Excel 格式，可同时上传多个文件
            </Text>
          </div>
        </div>
      </Card>

      {/* 模板下载 */}
      <Card title="数据模板" className="card">
        <Alert
          message="建议使用标准模板"
          description="为了确保数据格式正确，建议先下载标准模板，按照模板格式填写数据后再上传。"
          type="info"
          showIcon
          className="mb-4"
        />

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {templates.map((template, index) => (
            <div
              key={index}
              className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50"
            >
              <div className="flex items-center space-x-3">
                <FileTextOutlined className="text-blue-500" />
                <div>
                  <div className="font-medium">{template.name}</div>
                  <div className="text-sm text-gray-500">CSV格式</div>
                </div>
              </div>
              <Button
                type="text"
                icon={<DownloadOutlined />}
                onClick={() => downloadTemplate(template)}
              >
                下载
              </Button>
            </div>
          ))}
        </div>
      </Card>

      {/* 文件处理状态 */}
      <AnimatePresence>
        {files.length > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.3 }}
          >
            <Card title="文件处理状态" className="card">
              <div className="space-y-4">
                {files.map((file) => (
                  <motion.div
                    key={file.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 20 }}
                    className="p-4 border rounded-lg"
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center space-x-3">
                        {getFileIcon(file.file.name)}
                        <div>
                          <div className="font-medium">{file.file.name}</div>
                          <div className="text-sm text-gray-500">
                            {(file.file.size / 1024).toFixed(1)} KB
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center space-x-2">
                        {getStatusIcon(file.status)}
                        <Space>
                          {file.status === 'completed' && file.preview && (
                            <Button
                              type="text"
                              icon={<EyeOutlined />}
                              onClick={() => previewFileContent(file)}
                            >
                              预览
                            </Button>
                          )}
                          <Button
                            type="text"
                            icon={<DeleteOutlined />}
                            onClick={() => removeFile(file.id)}
                            danger
                          >
                            删除
                          </Button>
                        </Space>
                      </div>
                    </div>

                    {/* 进度条 */}
                    {['uploading', 'validating', 'processing'].includes(file.status) && (
                      <Progress
                        percent={Math.round(file.progress)}
                        status={file.status === 'error' ? 'exception' : 'active'}
                        className="mb-2"
                      />
                    )}

                    {/* 错误信息 */}
                    {file.status === 'error' && file.errors && (
                      <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg">
                        <Text type="danger" className="font-medium mb-2 block">
                          验证错误:
                        </Text>
                        <div className="space-y-1">
                          {file.errors.slice(0, 3).map((error, index) => (
                            <Text key={index} type="danger" className="text-sm block">
                              第{error.row}行 {error.field}: {error.message}
                            </Text>
                          ))}
                          {file.errors.length > 3 && (
                            <Text type="danger" className="text-sm">
                              还有 {file.errors.length - 3} 个错误...
                            </Text>
                          )}
                        </div>
                      </div>
                    )}

                    {/* 成功状态 */}
                    {file.status === 'completed' && (
                      <div className="mt-3 p-3 bg-green-50 border border-green-200 rounded-lg">
                        <Text type="success" className="font-medium">
                          文件处理完成！
                        </Text>
                      </div>
                    )}
                  </motion.div>
                ))}
              </div>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      {/* 预览模态框 */}
      <Modal
        title={`文件预览 - ${previewFile?.file.name}`}
        open={isModalVisible}
        onCancel={() => setIsModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setIsModalVisible(false)}>
            关闭
          </Button>,
        ]}
        width={800}
      >
        {previewFile?.preview && (
          <Table
            dataSource={previewFile.preview}
            columns={previewColumns}
            pagination={{ pageSize: 10 }}
            size="small"
          />
        )}
      </Modal>
    </motion.div>
  )
}

export default DataImport