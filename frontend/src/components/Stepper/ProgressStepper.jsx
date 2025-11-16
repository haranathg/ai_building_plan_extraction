function ProgressStepper({ currentStep }) {
  const steps = [
    { number: 1, label: 'Basic info' },
    { number: 2, label: 'Documents Upload' },
    { number: 3, label: 'Verification' }
  ];

  return (
    <div className="flex items-center justify-center mb-8">
      {steps.map((step, index) => (
        <div key={step.number} className="flex items-center">
          {/* Step Circle */}
          <div className="flex flex-col items-center">
            <div
              className={`
                w-10 h-10 rounded-full flex items-center justify-center font-semibold
                ${currentStep === step.number
                  ? 'bg-colab-blue text-white ring-4 ring-blue-200'
                  : currentStep > step.number
                  ? 'bg-colab-blue text-white'
                  : 'bg-gray-300 text-gray-600'
                }
              `}
            >
              {currentStep > step.number ? (
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              ) : (
                step.number
              )}
            </div>
            <span
              className={`
                mt-2 text-sm font-medium
                ${currentStep === step.number ? 'text-colab-blue' : 'text-gray-500'}
              `}
            >
              {step.label}
            </span>
          </div>

          {/* Connecting Line */}
          {index < steps.length - 1 && (
            <div
              className={`
                w-24 h-1 mx-2 mb-6
                ${currentStep > step.number ? 'bg-colab-blue' : 'bg-gray-300'}
              `}
            />
          )}
        </div>
      ))}
    </div>
  );
}

export default ProgressStepper;
