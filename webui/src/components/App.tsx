import { useState, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import logo from 'assets/logo.svg'

// 防抖Hook
function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value)

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value)
    }, delay)

    return () => {
      clearTimeout(handler)
    }
  }, [value, delay])

  return debouncedValue
}

// URL验证函数
function isValidBiliUrl(url: string): boolean {
  return url.startsWith('https://www.bilibili.com/video')
}

function App() {
  const [url, setUrl] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [summary, setSummary] = useState('')
  const [error, setError] = useState('')
  const [urlError, setUrlError] = useState('')

  // 防抖URL（300ms）
  const debouncedUrl = useDebounce(url, 300)

  // 验证URL格式
  useEffect(() => {
    if (debouncedUrl && !isValidBiliUrl(debouncedUrl)) {
      setUrlError('URL必须以 https://www.bilibili.com/video 开头')
    } else {
      setUrlError('')
    }
  }, [debouncedUrl])

  // 提交处理
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!debouncedUrl) {
      setError('请输入视频URL')
      return
    }

    if (!isValidBiliUrl(debouncedUrl)) {
      setError('URL格式不正确')
      return
    }

    setIsLoading(true)
    setError('')
    setSummary('')

    try {
      const response = await fetch('/api/summary_bili', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url: debouncedUrl }),
      })

      const data = await response.json()

      if (data.success) {
        setSummary(data.summary)
      } else {
        setError(data.error || '总结失败')
      }
    } catch (err) {
      setError('网络请求失败，请检查服务器是否运行')
      console.error(err)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8 text-center">
          <div className="mb-4 flex justify-center">
            <img src={logo} alt="Logo" className="h-16 w-16" />
          </div>
          <h1 className="text-4xl font-bold text-gray-900">
            B站视频智能总结
          </h1>
          <p className="mt-2 text-gray-600">
            输入B站视频链接，AI自动生成内容总结
          </p>
        </div>

        {/* Main Content */}
        <div className="mx-auto max-w-3xl">
          {/* Input Form */}
          <form onSubmit={handleSubmit} className="mb-6">
            <div className="rounded-lg bg-white p-6 shadow-lg">
              <label
                htmlFor="video-url"
                className="mb-2 block text-sm font-medium text-gray-700"
              >
                视频URL
              </label>
              <input
                id="video-url"
                type="text"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://www.bilibili.com/video/BV..."
                className={`w-full rounded-md border px-4 py-2 focus:outline-none focus:ring-2 ${
                  urlError
                    ? 'border-red-300 focus:ring-red-500'
                    : 'border-gray-300 focus:ring-indigo-500'
                }`}
                disabled={isLoading}
              />
              {urlError && (
                <p className="mt-1 text-sm text-red-600">{urlError}</p>
              )}

              <button
                type="submit"
                disabled={isLoading || !debouncedUrl || !!urlError}
                className="mt-4 w-full rounded-md bg-indigo-600 px-6 py-3 font-medium text-white transition hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:bg-gray-400"
              >
                {isLoading ? '处理中...' : '开始总结'}
              </button>
            </div>
          </form>

          {/* Loading */}
          {isLoading && (
            <div className="rounded-lg bg-white p-8 text-center shadow-lg">
              <div className="mx-auto h-12 w-12 animate-spin rounded-full border-4 border-indigo-200 border-t-indigo-600"></div>
              <p className="mt-4 text-gray-600">正在处理视频，请稍候...</p>
              <p className="mt-2 text-sm text-gray-400">
                这可能需要几分钟时间
              </p>
            </div>
          )}

          {/* Error */}
          {error && !isLoading && (
            <div className="rounded-lg bg-red-50 p-4 shadow-lg">
              <div className="flex">
                <div className="shrink-0">
                  <svg
                    className="h-5 w-5 text-red-400"
                    viewBox="0 0 20 20"
                    fill="currentColor"
                  >
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                      clipRule="evenodd"
                    />
                  </svg>
                </div>
                <div className="ml-3">
                  <p className="text-sm font-medium text-red-800">{error}</p>
                </div>
              </div>
            </div>
          )}

          {/* Summary Result */}
          {summary && !isLoading && (
            <div className="rounded-lg bg-white p-6 shadow-lg">
              <div className="mb-4 flex items-center justify-between">
                <h2 className="text-xl font-semibold text-gray-900">
                  总结结果
                </h2>
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(summary)
                    alert('已复制到剪贴板')
                  }}
                  className="rounded-md bg-gray-100 px-3 py-1 text-sm text-gray-700 transition hover:bg-gray-200"
                >
                  复制
                </button>
              </div>
              <div className="prose prose-slate max-w-none">
                <ReactMarkdown
                  components={{
                    // 自定义样式
                    h1: ({ node, ...props }) => (
                      <h1 className="text-2xl font-bold mb-4 mt-6" {...props} />
                    ),
                    h2: ({ node, ...props }) => (
                      <h2 className="text-xl font-bold mb-3 mt-5" {...props} />
                    ),
                    h3: ({ node, ...props }) => (
                      <h3 className="text-lg font-semibold mb-2 mt-4" {...props} />
                    ),
                    p: ({ node, ...props }) => (
                      <p className="mb-4 text-gray-700 leading-relaxed" {...props} />
                    ),
                    ul: ({ node, ...props }) => (
                      <ul className="list-disc list-inside mb-4 space-y-2" {...props} />
                    ),
                    ol: ({ node, ...props }) => (
                      <ol className="list-decimal list-inside mb-4 space-y-2" {...props} />
                    ),
                    li: ({ node, ...props }) => (
                      <li className="text-gray-700" {...props} />
                    ),
                    code: ({ node, ...props }) => {
                      const isInline = !props.className
                      return isInline ? (
                        <code
                          className="bg-gray-100 text-red-600 px-1 py-0.5 rounded text-sm"
                          {...props}
                        />
                      ) : (
                        <code
                          className="block bg-gray-100 p-4 rounded-lg text-sm overflow-x-auto"
                          {...props}
                        />
                      )
                    },
                    blockquote: ({ node, ...props }) => (
                      <blockquote
                        className="border-l-4 border-indigo-500 pl-4 italic text-gray-600 my-4"
                        {...props}
                      />
                    ),
                    strong: ({ node, ...props }) => (
                      <strong className="font-bold text-gray-900" {...props} />
                    ),
                    em: ({ node, ...props }) => (
                      <em className="italic text-gray-700" {...props} />
                    ),
                  }}
                >
                  {summary}
                </ReactMarkdown>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default App
