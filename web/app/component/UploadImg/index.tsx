'use client'
import { InboxOutlined } from '@ant-design/icons'
import type { UploadProps } from 'antd'
import { message, Upload, Row, Col } from 'antd'
import SearchResult from '@/app/component/SearchResult/index'
import { useState } from 'react'
import styles from './index.module.css'
const { Dragger } = Upload

export interface ImgResult {
  id: number
  distance: number
  file_name: string
  file_path: string
}

const getObjectUrl = (file) => {
  if (!file?.type.startsWith('image/')) {
    console.error('非图片文件')
    return
  }

  // 生成对象URL
  const objectUrl = URL.createObjectURL(file)
  return objectUrl
}

const demoImgList = ['1.jpeg', '2.jpeg', '3.jpeg', '6.jpeg', '5.jpeg']

export default function UploadImg() {
  // 所选图片预览 URL
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)

  // 搜索结果
  const [imgResultList, setImgResultList] = useState<ImgResult[]>([])

  // 是否搜索完毕
  const [showSearchResult, setShowSearchResult] = useState(false)

  // 将网络图片转换为 File 对象
  const convertUrlToFile = async (url) => {
    try {
      const response = await fetch(url)
      const blob = await response.blob()
      return new File([blob], 'image.jpg', { type: blob.type })
    } catch (error) {
      console.error('转换失败:', error)
      return null
    }
  }

  const handleImgClick = async (e) => {
    const res = await convertUrlToFile(e?.target?.src || '')

    const formData = new FormData()
    formData.append('file', res)

    const response = await fetch('/api/search', {
      method: 'POST',
      body: formData,
    })

    if (response.ok) {
      // 设置预览图
      const objectUrl = getObjectUrl(res)
      setPreviewUrl(objectUrl)

      const resultList = await response.json()
      setShowSearchResult(true)
      setImgResultList(resultList)
    }
  }

  const beforeUpload = (file) => {
    const supportImgTypeList = ['image/png', 'image/jpeg', 'image/jpg']

    const isSupportImg = supportImgTypeList?.includes(file.type)

    if (!isSupportImg) {
      message.error(`${file.name} is not a png file`)
    }

    const isLt2M = file.size / 1024 / 1024 < 200
    if (!isLt2M) {
      message.error('Image must smaller than 200MB!')
    }

    return isSupportImg || Upload.LIST_IGNORE
  }

  const props: UploadProps = {
    name: 'file',
    action: '/api/search',
    onChange(info) {
      const { status } = info.file
      if (status !== 'uploading') {
        console.log('uploading', info.file, info.fileList)
      }
      if (status === 'done') {
        const objectUrl = getObjectUrl(info.file.originFileObj)
        setPreviewUrl(objectUrl)
        setShowSearchResult(true)
        setImgResultList(info.file.response)
      } else if (status === 'error') {
        message.error(`${info.file.name} file upload failed.`)
      }
    },
    beforeUpload,
  }

  return showSearchResult ? (
    <SearchResult
      uploadProps={props}
      imgResultList={imgResultList}
      previewUrl={previewUrl}
      demoImgList={demoImgList}
      handleImgClick={handleImgClick}
    />
  ) : (
    <div className="p-6 w-full h-full">
      <Row gutter={[24, 24]} className="text-center mt-12">
        <Col span={24}>
          <div className="text-[36px] text-[#132039] font-semibold mb-1">
            萌兽搜搜
          </div>
          <div className="text-[#000000a6] text-sm tracking-[1.75px]">
            使用 OceanBase 向量搜索相似的哺乳动物或鸟类图片
          </div>
        </Col>
        <Col span={24} className={styles.uploadWrapper}>
          <Dragger {...props}>
            <p className="ant-upload-drag-icon">
              <InboxOutlined />
            </p>
            <p className="ant-upload-text text-[14px]">
              拖拽哺乳动物或鸟类图片到此处 或 <a>选择文件</a>
            </p>
            <p className="ant-upload-hint text-xs">
              文件大小不超过 200 MB，格式支持 .jpg，.jpeg，.png
            </p>
          </Dragger>
        </Col>
        <Col span={24}>
          <div className="mb-2">没有图片没关系，可以试试这些图片</div>
          <div className={`flex justify-between gap-4`}>
            {demoImgList?.map((item) => {
              return (
                <div
                  key={item}
                  className="relative aspect-square w-[calc(33.333%_-_16px)]
                  cursor-pointer h-full flex justify-center items-center overflow-hidden  rounded-md
                  "
                >
                  <div className="text-xs text-white leading-[18px] w-[32px] h-[18px] bg-black rounded-lg opacity-60 absolute top-2.5 right-2.5">
                    示例
                  </div>
                  <img
                    alt={item}
                    className="w-full h-full object-cover object-center"
                    src={`${process.env.ASSET_PREFIX}/image/${item}`}
                    preview={false}
                    onClick={handleImgClick}
                  />
                </div>
              )
            })}
          </div>
        </Col>
      </Row>
    </div>
  )
}
