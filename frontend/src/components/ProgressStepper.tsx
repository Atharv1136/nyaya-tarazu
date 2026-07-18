type StepStatus = 'pending' | 'active' | 'done' | 'error'

interface Step {
  id: string
  label: string
  status: StepStatus
}

interface ProgressStepperProps {
  steps: Step[]
}

export default function ProgressStepper({ steps }: ProgressStepperProps) {
  return (
    <div className="stepper" role="status" aria-live="polite" id="progress-stepper">
      {steps.map((step) => (
        <div
          key={step.id}
          className={`stepper-item ${step.status}`}
          aria-label={`${step.label}: ${step.status}`}
        >
          <div className="stepper-dot" />
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ fontSize: 'var(--text-sm)' }}>{step.label}</span>
            {step.status === 'active' && (
              <div
                className="spinner"
                style={{ width: 14, height: 14 }}
                aria-hidden="true"
              />
            )}
            {step.status === 'done' && (
              <span
                aria-hidden="true"
                style={{ color: 'var(--brass)', fontSize: 'var(--text-xs)' }}
              >
                ✓
              </span>
            )}
            {step.status === 'error' && (
              <span
                aria-hidden="true"
                style={{ color: 'var(--oxblood)', fontSize: 'var(--text-xs)' }}
              >
                ✕
              </span>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}

export type { Step, StepStatus }
