import React from 'react'

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, info) {
    // eslint-disable-next-line no-console
    console.error('ErrorBoundary caught:', error, info)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="rounded-xl border border-rose-200 dark:border-rose-400/30 bg-rose-50 dark:bg-rose-950/60 p-4">
          <div className="text-rose-800 dark:text-rose-200 font-semibold mb-1">An error occurred rendering this page.</div>
          <div className="text-xs text-rose-700 dark:text-rose-300 break-all">{String(this.state.error)}</div>
        </div>
      )
    }
    return this.props.children
  }
}

