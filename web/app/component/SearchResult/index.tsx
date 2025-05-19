'use client'
import { Upload, Row, Col, Button, Image } from 'antd'
import styles from './index.module.css'
import type { ImgResult } from '@/app/component/UploadImg'

export default function SearchResult({
  imgResultList,
  previewUrl = '',
  uploadProps,
  demoImgList = [],
  handleImgClick,
}: {
  imgResultList: ImgResult[]
  previewUrl: string | null
  uploadProps: any
  demoImgList: string[]
  handleImgClick: (e: any) => Promise<void>
}) {
  return (
    <div className="m-12 bg-[#f5f8ff]   border border-solid border-gray-200 rounded-md">
      <Row>
        <Col span={6} className="p-6">
          <Row gutter={[24, 24]} className="p-6">
            <Col span={24}>
              <span className="text-[16px] text-[#132039] font-semibold">
                上传图片
              </span>
            </Col>
            <Col span={24}>
              <div className="rounded-md cursor-pointer">
                <Image src={previewUrl} alt="" preview={false} />
              </div>
            </Col>
            <Col span={24} className={styles.uploadWrapper}>
              <Upload
                {...uploadProps}
                className="avatar-uploader"
                style={{ width: '100%' }}
              >
                <Button
                  type="primary"
                  size="large"
                  className="w-full text-[14px] "
                >
                  重新上传
                </Button>
              </Upload>
            </Col>
            <Col span={24}>
              <div className="mb-2">没有图片没关系，可以试试这些图片</div>
              <div className={`flex flex-wrap gap-2`}>
                {demoImgList?.map((item) => {
                  return (
                    <div
                      key={item}
                      className="cursor-pointer aspect-square w-[calc(33.333%_-_8px)] justify-center items-center overflow-hidden  rounded-md"
                    >
                      <img
                        src={`${process.env.ASSET_PREFIX}/image/${item}`}
                        className="w-full h-full object-cover object-center"
                        preview={false}
                        alt={item}
                        onClick={handleImgClick}
                      />
                    </div>
                  )
                })}
              </div>
            </Col>
          </Row>
        </Col>
        <Col span={18} className="border-l border-solid border-[#e2e8f3] p-6">
          <Row gutter={[24, 24]} className="p-6">
            <Col span={24}>
              <span className="text-[16px] text-[#132039] font-semibold">
                相关结果
              </span>
            </Col>
            <Col span={24}>
              <div className={`flex justify-between flex-wrap gap-2`}>
                {imgResultList?.map((item) => {
                  return (
                    <div
                      key={item?.id}
                      className="aspect-square w-[calc(33.333%_-_8px)]  mb-2 min-w-[230px]"
                    >
                      <div className="cursor-pointer w-full h-full  flex justify-center items-center mb-2 overflow-hidden  rounded-md">
                        <img
                          alt={item.file_name}
                          src={`${
                            process.env.NODE_ENV === 'development'
                              ? process.env.NEXT_PUBLIC_URL
                              : ''
                          }${item.file_path}`}
                          className="w-full h-full object-cover transition-transform duration-300 ease-in-out hover:scale-110"
                          preview={false}
                        />
                      </div>
                      <div>距离值:{item.distance}</div>
                    </div>
                  )
                })}
              </div>
            </Col>
          </Row>
        </Col>
      </Row>
    </div>
  )
}
