export type Status = 'PASSED' | 'FAILED' | 'SKIPPED' | 'ERROR'

export interface TestResult {
  id: string
  test_file: string
  test_name: string
  status: Status
  duration: number    // ms
  coverage: number    // 0-100
  error_message: string | null
}

export interface TestSession {
  _file: string
  name: string
  timestamp: number
  results: TestResult[]
}

export const STATUS_COLOR: Record<Status, string> = {
  PASSED:  '#00ff88',
  FAILED:  '#ff2d55',
  SKIPPED: '#ffb800',
  ERROR:   '#fb923c',
}
