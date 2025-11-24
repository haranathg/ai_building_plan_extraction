import React, { useState, useEffect } from 'react';
import { 
  Building2, Upload, FileCheck, AlertTriangle, CheckCircle2, 
  ChevronRight, ChevronLeft, FileText, Download, Send, 
  Clock, Save, X, Plus, Trash2, Eye, Home, User, Settings,
  HelpCircle, LogOut, Bell, Search, Compass, Shield, Zap,
  FileWarning, CheckSquare, XCircle, Info, ArrowRight, Loader2,
  Menu, MapPin, Calendar, Hash
} from 'lucide-react';

// Design System Colors
const colors = {
  primary: '#1a365d',      // Deep navy - trust, authority
  primaryLight: '#2c5282',
  primaryDark: '#0f2540',
  accent: '#38a169',       // Success green
  accentWarm: '#dd6b20',   // Warning orange
  accentDanger: '#e53e3e', // Error red
  surface: '#f7fafc',
  surfaceWhite: '#ffffff',
  text: '#1a202c',
  textMuted: '#718096',
  border: '#e2e8f0',
  borderFocus: '#4299e1',
};

// ===== HEADER COMPONENT =====
const Header = ({ currentStep, userName = "Sarah Mitchell" }) => (
  <header className="bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 text-white shadow-xl sticky top-0 z-50">
    <div className="max-w-7xl mx-auto">
      {/* Top bar */}
      <div className="flex items-center justify-between px-6 py-3 border-b border-slate-700/50">
        <div className="flex items-center gap-4">
          {/* Logo */}
          <div className="flex items-center gap-3">
            <div className="relative">
              <div className="w-10 h-10 bg-gradient-to-br from-emerald-400 to-teal-500 rounded-xl flex items-center justify-center shadow-lg shadow-emerald-500/20">
                <Shield className="w-6 h-6 text-white" />
              </div>
              <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-amber-400 rounded-full flex items-center justify-center">
                <Zap className="w-2.5 h-2.5 text-slate-900" />
              </div>
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight">CompliCheck<span className="text-emerald-400">AI</span></h1>
              <div className="flex items-center gap-1.5 text-xs text-slate-400">
                <span>powered by</span>
                <Compass className="w-3 h-3 text-amber-400" />
                <span className="font-semibold text-amber-400">UrbanCompass</span>
              </div>
            </div>
          </div>
        </div>
        
        {/* Right side controls */}
        <div className="flex items-center gap-4">
          <button className="p-2 hover:bg-slate-700/50 rounded-lg transition-colors relative">
            <Bell className="w-5 h-5 text-slate-400" />
            <span className="absolute top-1 right-1 w-2 h-2 bg-emerald-400 rounded-full"></span>
          </button>
          <button className="p-2 hover:bg-slate-700/50 rounded-lg transition-colors">
            <HelpCircle className="w-5 h-5 text-slate-400" />
          </button>
          <div className="h-6 w-px bg-slate-700"></div>
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-gradient-to-br from-violet-500 to-purple-600 rounded-full flex items-center justify-center text-sm font-semibold">
              SM
            </div>
            <div className="hidden md:block text-right">
              <p className="text-sm font-medium">{userName}</p>
              <p className="text-xs text-slate-400">Architect</p>
            </div>
          </div>
        </div>
      </div>
      
      {/* Navigation */}
      <nav className="px-6 py-2">
        <div className="flex items-center gap-6 text-sm">
          <a href="#" className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors py-2">
            <Home className="w-4 h-4" />
            Dashboard
          </a>
          <a href="#" className="flex items-center gap-2 text-white border-b-2 border-emerald-400 py-2 font-medium">
            <FileCheck className="w-4 h-4" />
            New Submission
          </a>
          <a href="#" className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors py-2">
            <Clock className="w-4 h-4" />
            Drafts
          </a>
          <a href="#" className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors py-2">
            <FileText className="w-4 h-4" />
            History
          </a>
        </div>
      </nav>
    </div>
  </header>
);

// ===== FOOTER COMPONENT =====
const Footer = () => (
  <footer className="bg-slate-900 text-slate-400 mt-auto">
    <div className="max-w-7xl mx-auto px-6 py-8">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
        <div className="col-span-1 md:col-span-2">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-8 h-8 bg-gradient-to-br from-emerald-400 to-teal-500 rounded-lg flex items-center justify-center">
              <Shield className="w-5 h-5 text-white" />
            </div>
            <span className="text-lg font-bold text-white">CompliCheck<span className="text-emerald-400">AI</span></span>
          </div>
          <p className="text-sm text-slate-500 max-w-md">
            Streamlining building consent submissions with AI-powered validation. 
            Ensuring compliance, reducing delays, and simplifying the approval process.
          </p>
          <div className="flex items-center gap-2 mt-4 text-xs">
            <Compass className="w-4 h-4 text-amber-400" />
            <span className="text-amber-400 font-medium">Powered by UrbanCompass</span>
          </div>
        </div>
        <div>
          <h4 className="font-semibold text-white mb-3">Resources</h4>
          <ul className="space-y-2 text-sm">
            <li><a href="#" className="hover:text-white transition-colors">Documentation</a></li>
            <li><a href="#" className="hover:text-white transition-colors">Building Code Guide</a></li>
            <li><a href="#" className="hover:text-white transition-colors">API Access</a></li>
          </ul>
        </div>
        <div>
          <h4 className="font-semibold text-white mb-3">Support</h4>
          <ul className="space-y-2 text-sm">
            <li><a href="#" className="hover:text-white transition-colors">Help Center</a></li>
            <li><a href="#" className="hover:text-white transition-colors">Contact Us</a></li>
            <li><a href="#" className="hover:text-white transition-colors">Report Issue</a></li>
          </ul>
        </div>
      </div>
      <div className="border-t border-slate-800 mt-8 pt-6 flex flex-col md:flex-row justify-between items-center gap-4">
        <p className="text-xs">© 2025 CompliCheckAI by UrbanCompass. All rights reserved.</p>
        <div className="flex items-center gap-6 text-xs">
          <a href="#" className="hover:text-white transition-colors">Privacy Policy</a>
          <a href="#" className="hover:text-white transition-colors">Terms of Service</a>
          <a href="#" className="hover:text-white transition-colors">Cookie Settings</a>
        </div>
      </div>
    </div>
  </footer>
);

// ===== PROGRESS STEPPER =====
const ProgressStepper = ({ currentStep, steps }) => (
  <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 mb-6">
    <div className="flex items-center justify-between relative">
      {/* Progress line */}
      <div className="absolute top-5 left-0 right-0 h-0.5 bg-slate-200">
        <div 
          className="h-full bg-gradient-to-r from-emerald-500 to-teal-500 transition-all duration-500"
          style={{ width: `${((currentStep - 1) / (steps.length - 1)) * 100}%` }}
        />
      </div>
      
      {steps.map((step, index) => {
        const stepNum = index + 1;
        const isActive = stepNum === currentStep;
        const isComplete = stepNum < currentStep;
        
        return (
          <div key={step.id} className="flex flex-col items-center relative z-10">
            <div className={`
              w-10 h-10 rounded-full flex items-center justify-center text-sm font-semibold
              transition-all duration-300 shadow-md
              ${isComplete ? 'bg-gradient-to-br from-emerald-500 to-teal-500 text-white' : ''}
              ${isActive ? 'bg-white border-2 border-emerald-500 text-emerald-600 ring-4 ring-emerald-100' : ''}
              ${!isActive && !isComplete ? 'bg-slate-100 text-slate-400 border-2 border-slate-200' : ''}
            `}>
              {isComplete ? <CheckCircle2 className="w-5 h-5" /> : stepNum}
            </div>
            <span className={`
              mt-2 text-xs font-medium text-center max-w-20
              ${isActive ? 'text-emerald-600' : ''}
              ${isComplete ? 'text-slate-600' : ''}
              ${!isActive && !isComplete ? 'text-slate-400' : ''}
            `}>
              {step.label}
            </span>
          </div>
        );
      })}
    </div>
  </div>
);

// ===== STEP 1: PROJECT OVERVIEW (NEW) =====
const Step1ProjectOverview = ({ data, setData, onNext }) => {
  const [formData, setFormData] = useState(data.projectOverview || {
    projectName: '',
    description: ''
  });

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSubmit = () => {
    setData(prev => ({ ...prev, projectOverview: formData }));
    onNext();
  };

  const isValid = formData.projectName && formData.projectName.trim().length > 0;

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="bg-gradient-to-r from-slate-50 to-white px-6 py-4 border-b border-slate-200">
          <h2 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
            <FileText className="w-5 h-5 text-emerald-600" />
            New Project
          </h2>
          <p className="text-sm text-slate-500 mt-1">Let's start with the basics about your project</p>
        </div>
        
        <div className="p-6 space-y-6">
          {/* Welcome message */}
          <div className="bg-gradient-to-br from-emerald-50 to-teal-50 rounded-xl p-5 border border-emerald-100">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 bg-gradient-to-br from-emerald-500 to-teal-500 rounded-xl flex items-center justify-center flex-shrink-0">
                <Zap className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className="font-semibold text-emerald-800">Welcome to CompliCheckAI</h3>
                <p className="text-sm text-emerald-700 mt-1">
                  We'll guide you through the pre-submission validation process for your building consent application. 
                  Start by telling us about your project.
                </p>
              </div>
            </div>
          </div>

          {/* Project Name */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              Project Name <span className="text-rose-500">*</span>
            </label>
            <input
              type="text"
              value={formData.projectName}
              onChange={(e) => handleChange('projectName', e.target.value)}
              placeholder="e.g., Smith Family Residence, 42 Greenview Lane Development"
              className="w-full px-4 py-3 rounded-xl border border-slate-300 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all text-lg"
            />
            <p className="text-xs text-slate-400 mt-2">Choose a memorable name to identify this project</p>
          </div>

          {/* Project Description */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              Project Description <span className="text-rose-500">*</span>
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => handleChange('description', e.target.value)}
              rows={6}
              placeholder="Describe your proposed building work in detail. Include information about:
• Type of construction (new build, renovation, addition)
• Key features and specifications
• Any special requirements or considerations
• Purpose of the building"
              className="w-full px-4 py-3 rounded-xl border border-slate-300 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all resize-none"
            />
            <p className="text-xs text-slate-400 mt-2">
              A detailed description helps our AI provide accurate document requirements
            </p>
          </div>

          {/* Tips */}
          <div className="bg-blue-50 rounded-xl p-4 border border-blue-100">
            <h4 className="font-medium text-blue-800 flex items-center gap-2 mb-2">
              <Info className="w-4 h-4" />
              Tips for a good description
            </h4>
            <ul className="text-sm text-blue-700 space-y-1">
              <li>• Mention the number of bedrooms, bathrooms, and stories</li>
              <li>• Include approximate building area if known</li>
              <li>• Note any special features (basement, garage, deck, pool)</li>
              <li>• Describe the construction type (timber frame, concrete, steel)</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="flex justify-between items-center">
        <button className="flex items-center gap-2 px-5 py-2.5 text-slate-600 hover:text-slate-800 transition-colors">
          <Save className="w-4 h-4" />
          Save Draft
        </button>
        <button
          onClick={handleSubmit}
          disabled={!isValid}
          className={`flex items-center gap-2 px-6 py-3 rounded-xl font-medium transition-all shadow-lg ${
            isValid
              ? 'bg-gradient-to-r from-emerald-600 to-teal-600 text-white hover:from-emerald-700 hover:to-teal-700 shadow-emerald-500/20'
              : 'bg-slate-200 text-slate-400 cursor-not-allowed'
          }`}
        >
          Continue
          <ChevronRight className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
};

// ===== STEP 2: PROJECT DETAILS =====
const Step2ProjectDetails = ({ data, setData, onNext, onBack }) => {
  const [formData, setFormData] = useState(data.projectDetails || {
    address: '',
    consentType: 'new-dwelling',
    bedrooms: '3',
    stories: '2',
    buildingArea: '',
    landArea: '',
    zoningDistrict: ''
  });

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSubmit = () => {
    setData(prev => ({ ...prev, projectDetails: formData }));
    onNext();
  };

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="bg-gradient-to-r from-slate-50 to-white px-6 py-4 border-b border-slate-200">
          <h2 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
            <Building2 className="w-5 h-5 text-emerald-600" />
            Project Details
          </h2>
          <p className="text-sm text-slate-500 mt-1">Enter the specifications for your building consent application</p>
        </div>

        {/* Project context banner */}
        {data.projectOverview?.projectName && (
          <div className="px-6 py-3 bg-slate-50 border-b border-slate-200">
            <p className="text-sm text-slate-600">
              <span className="font-medium">Project:</span> {data.projectOverview.projectName}
            </p>
          </div>
        )}
        
        <div className="p-6 space-y-6">
          {/* Consent Type */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Consent Type <span className="text-rose-500">*</span>
              </label>
              <select
                value={formData.consentType}
                onChange={(e) => handleChange('consentType', e.target.value)}
                className="w-full px-4 py-3 rounded-xl border border-slate-300 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all bg-white"
              >
                <option value="new-dwelling">New Dwelling</option>
                <option value="alteration">Alteration to Existing</option>
                <option value="addition">Addition</option>
                <option value="commercial">Commercial Building</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Zoning District
              </label>
              <select
                value={formData.zoningDistrict}
                onChange={(e) => handleChange('zoningDistrict', e.target.value)}
                className="w-full px-4 py-3 rounded-xl border border-slate-300 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all bg-white"
              >
                <option value="">Select zoning district...</option>
                <option value="residential-single">Residential - Single House</option>
                <option value="residential-mixed">Residential - Mixed Housing Suburban</option>
                <option value="residential-urban">Residential - Mixed Housing Urban</option>
                <option value="residential-terraced">Residential - Terrace Housing</option>
                <option value="business-local">Business - Local Centre</option>
                <option value="business-mixed">Business - Mixed Use</option>
              </select>
            </div>
          </div>

          {/* Address */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              <MapPin className="w-4 h-4 inline mr-1" />
              Site Address <span className="text-rose-500">*</span>
            </label>
            <input
              type="text"
              value={formData.address}
              onChange={(e) => handleChange('address', e.target.value)}
              placeholder="Enter full property address"
              className="w-full px-4 py-3 rounded-xl border border-slate-300 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all"
            />
          </div>

          {/* Building Specs */}
          <div className="bg-slate-50 rounded-xl p-5 space-y-4">
            <h3 className="font-medium text-slate-800">Building Specifications</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1.5">Bedrooms</label>
                <select
                  value={formData.bedrooms}
                  onChange={(e) => handleChange('bedrooms', e.target.value)}
                  className="w-full px-3 py-2.5 rounded-lg border border-slate-300 text-sm focus:ring-2 focus:ring-emerald-500 bg-white"
                >
                  {[1,2,3,4,5,6].map(n => <option key={n} value={n}>{n}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1.5">Stories</label>
                <select
                  value={formData.stories}
                  onChange={(e) => handleChange('stories', e.target.value)}
                  className="w-full px-3 py-2.5 rounded-lg border border-slate-300 text-sm focus:ring-2 focus:ring-emerald-500 bg-white"
                >
                  {[1,2,3,4].map(n => <option key={n} value={n}>{n}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1.5">Building Area (m²)</label>
                <input
                  type="number"
                  value={formData.buildingArea}
                  onChange={(e) => handleChange('buildingArea', e.target.value)}
                  placeholder="e.g., 185"
                  className="w-full px-3 py-2.5 rounded-lg border border-slate-300 text-sm focus:ring-2 focus:ring-emerald-500"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1.5">Land Area (m²)</label>
                <input
                  type="number"
                  value={formData.landArea}
                  onChange={(e) => handleChange('landArea', e.target.value)}
                  placeholder="e.g., 650"
                  className="w-full px-3 py-2.5 rounded-lg border border-slate-300 text-sm focus:ring-2 focus:ring-emerald-500"
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="flex justify-between items-center">
        <div className="flex items-center gap-3">
          <button onClick={onBack} className="flex items-center gap-2 px-5 py-2.5 text-slate-600 hover:text-slate-800 transition-colors">
            <ChevronLeft className="w-5 h-5" />
            Back
          </button>
          <button className="flex items-center gap-2 px-5 py-2.5 text-slate-600 hover:text-slate-800 transition-colors">
            <Save className="w-4 h-4" />
            Save Draft
          </button>
        </div>
        <button
          onClick={handleSubmit}
          className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-emerald-600 to-teal-600 text-white rounded-xl font-medium hover:from-emerald-700 hover:to-teal-700 transition-all shadow-lg shadow-emerald-500/20"
        >
          Continue to Analysis
          <ChevronRight className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
};

// ===== STEP 3: SYSTEM ANALYSIS =====
const Step3SystemAnalysis = ({ data, onNext, onBack }) => {
  const [analyzing, setAnalyzing] = useState(true);
  const [progress, setProgress] = useState(0);
  const [analysisComplete, setAnalysisComplete] = useState(false);

  useEffect(() => {
    const timer = setInterval(() => {
      setProgress(prev => {
        if (prev >= 100) {
          clearInterval(timer);
          setTimeout(() => {
            setAnalyzing(false);
            setAnalysisComplete(true);
          }, 500);
          return 100;
        }
        return prev + 2;
      });
    }, 50);
    return () => clearInterval(timer);
  }, []);

  const analysisSteps = [
    { label: 'Parsing project details', complete: progress > 15 },
    { label: 'Checking zoning requirements', complete: progress > 30 },
    { label: 'Analyzing building code compliance', complete: progress > 50 },
    { label: 'Determining required documents', complete: progress > 70 },
    { label: 'Preparing checklist', complete: progress > 90 },
  ];

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="bg-gradient-to-r from-slate-50 to-white px-6 py-4 border-b border-slate-200">
          <h2 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
            <Zap className="w-5 h-5 text-amber-500" />
            AI-Powered Analysis
          </h2>
          <p className="text-sm text-slate-500 mt-1">Interpreting your project against the knowledge base</p>
        </div>

        <div className="p-6">
          {analyzing ? (
            <div className="space-y-6">
              {/* Progress bar */}
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-slate-600">Analyzing requirements...</span>
                  <span className="font-medium text-emerald-600">{progress}%</span>
                </div>
                <div className="h-3 bg-slate-100 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-gradient-to-r from-emerald-500 via-teal-500 to-emerald-500 transition-all duration-300 animate-pulse"
                    style={{ width: `${progress}%` }}
                  />
                </div>
              </div>

              {/* Analysis steps */}
              <div className="space-y-3">
                {analysisSteps.map((step, i) => (
                  <div key={i} className={`flex items-center gap-3 p-3 rounded-lg transition-all ${step.complete ? 'bg-emerald-50' : 'bg-slate-50'}`}>
                    {step.complete ? (
                      <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                    ) : (
                      <Loader2 className="w-5 h-5 text-slate-400 animate-spin" />
                    )}
                    <span className={step.complete ? 'text-emerald-700' : 'text-slate-500'}>{step.label}</span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Success message */}
              <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4 flex items-start gap-3">
                <CheckCircle2 className="w-6 h-6 text-emerald-600 flex-shrink-0 mt-0.5" />
                <div>
                  <h3 className="font-semibold text-emerald-800">Analysis Complete</h3>
                  <p className="text-sm text-emerald-700 mt-1">
                    Based on your 3-bedroom, 2-story new dwelling in the {data.projectDetails?.zoningDistrict || 'residential'} zone, 
                    we've identified the required documentation for your consent application.
                  </p>
                </div>
              </div>

              {/* Summary cards */}
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl p-4 border border-blue-100">
                  <div className="text-2xl font-bold text-blue-700">14</div>
                  <div className="text-sm text-blue-600">Required Documents</div>
                </div>
                <div className="bg-gradient-to-br from-amber-50 to-orange-50 rounded-xl p-4 border border-amber-100">
                  <div className="text-2xl font-bold text-amber-700">3</div>
                  <div className="text-sm text-amber-600">Building Code Clauses</div>
                </div>
                <div className="bg-gradient-to-br from-emerald-50 to-teal-50 rounded-xl p-4 border border-emerald-100">
                  <div className="text-2xl font-bold text-emerald-700">~20</div>
                  <div className="text-sm text-emerald-600">Days (Est. Processing)</div>
                </div>
              </div>

              {/* Identified requirements */}
              <div className="bg-slate-50 rounded-xl p-5">
                <h3 className="font-medium text-slate-800 mb-3">Key Compliance Areas Identified</h3>
                <div className="grid grid-cols-2 gap-3">
                  {['Structural (B1)', 'Durability (B2)', 'Fire Safety (C)', 'Access (D)', 'Moisture (E2)', 'Services (G)'].map((item, i) => (
                    <div key={i} className="flex items-center gap-2 text-sm text-slate-600">
                      <CheckSquare className="w-4 h-4 text-emerald-500" />
                      {item}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Actions */}
      <div className="flex justify-between items-center">
        <button onClick={onBack} className="flex items-center gap-2 px-5 py-2.5 text-slate-600 hover:text-slate-800 transition-colors">
          <ChevronLeft className="w-5 h-5" />
          Back
        </button>
        <button
          onClick={onNext}
          disabled={analyzing}
          className={`flex items-center gap-2 px-6 py-3 rounded-xl font-medium transition-all shadow-lg ${
            analyzing 
              ? 'bg-slate-200 text-slate-400 cursor-not-allowed' 
              : 'bg-gradient-to-r from-emerald-600 to-teal-600 text-white hover:from-emerald-700 hover:to-teal-700 shadow-emerald-500/20'
          }`}
        >
          View Required Documents
          <ChevronRight className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
};

// ===== STEP 4: REQUIRED DOCUMENTS LIST =====
const Step4RequiredDocuments = ({ data, setData, onNext, onBack }) => {
  const requiredDocs = [
    { id: 'ba2', name: 'Building Consent Application Form (BA2)', category: 'Forms', required: true },
    { id: 'ownership', name: 'Certificate of Title / Ownership Evidence', category: 'Legal', required: true },
    { id: 'site-plan', name: 'Site Plan (1:200 scale)', category: 'Drawings', required: true },
    { id: 'floor-plans', name: 'Floor Plans (all levels)', category: 'Drawings', required: true },
    { id: 'elevations', name: 'Building Elevations (all faces)', category: 'Drawings', required: true },
    { id: 'sections', name: 'Cross Sections', category: 'Drawings', required: true },
    { id: 'structural', name: 'Structural Engineering Plans', category: 'Engineering', required: true },
    { id: 'structural-calcs', name: 'Structural Calculations', category: 'Engineering', required: true },
    { id: 'geotech', name: 'Geotechnical Report', category: 'Reports', required: true },
    { id: 'specs', name: 'Building Specifications', category: 'Documentation', required: true },
    { id: 'branz', name: 'Product Specifications / BRANZ Appraisals', category: 'Documentation', required: true },
    { id: 'energy', name: 'Energy Compliance (H1)', category: 'Compliance', required: true },
    { id: 'fire', name: 'Fire Safety Schedule (if applicable)', category: 'Compliance', required: false },
    { id: 'drainage', name: 'Drainage & Plumbing Plans', category: 'Services', required: true },
  ];

  const categories = [...new Set(requiredDocs.map(d => d.category))];

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="bg-gradient-to-r from-slate-50 to-white px-6 py-4 border-b border-slate-200">
          <h2 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
            <FileText className="w-5 h-5 text-blue-600" />
            Required Documents Checklist
          </h2>
          <p className="text-sm text-slate-500 mt-1">14 documents required for your new dwelling consent application</p>
        </div>

        <div className="p-6 space-y-6">
          {/* Info banner */}
          <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 flex items-start gap-3">
            <Info className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-blue-700">
              Documents marked with <span className="text-rose-500 font-medium">*</span> are mandatory. 
              Ensure all drawings are to scale and specifications are clearly referenced.
            </div>
          </div>

          {/* Documents by category */}
          <div className="space-y-6">
            {categories.map(category => (
              <div key={category}>
                <h3 className="text-sm font-semibold text-slate-700 uppercase tracking-wider mb-3 flex items-center gap-2">
                  <span className="w-2 h-2 bg-emerald-500 rounded-full"></span>
                  {category}
                </h3>
                <div className="space-y-2">
                  {requiredDocs.filter(d => d.category === category).map(doc => (
                    <div key={doc.id} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg hover:bg-slate-100 transition-colors">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 bg-white rounded-lg border border-slate-200 flex items-center justify-center">
                          <FileText className="w-4 h-4 text-slate-400" />
                        </div>
                        <span className="text-sm text-slate-700">
                          {doc.name}
                          {doc.required && <span className="text-rose-500 ml-1">*</span>}
                        </span>
                      </div>
                      <span className={`text-xs px-2 py-1 rounded-full ${doc.required ? 'bg-rose-100 text-rose-700' : 'bg-slate-200 text-slate-600'}`}>
                        {doc.required ? 'Required' : 'Optional'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="flex justify-between items-center">
        <button onClick={onBack} className="flex items-center gap-2 px-5 py-2.5 text-slate-600 hover:text-slate-800 transition-colors">
          <ChevronLeft className="w-5 h-5" />
          Back
        </button>
        <button
          onClick={onNext}
          className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-emerald-600 to-teal-600 text-white rounded-xl font-medium hover:from-emerald-700 hover:to-teal-700 transition-all shadow-lg shadow-emerald-500/20"
        >
          Upload Documents
          <ChevronRight className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
};

// ===== STEP 5: UPLOAD DOCUMENTS =====
const Step5UploadDocuments = ({ data, setData, onNext, onBack }) => {
  const [uploads, setUploads] = useState({
    'ba2': { file: null, status: 'pending' },
    'ownership': { file: null, status: 'pending' },
    'site-plan': { file: { name: 'Site_Plan_v2.pdf', size: 2400000 }, status: 'uploaded' },
    'floor-plans': { file: { name: 'Floor_Plans_All_Levels.pdf', size: 4800000 }, status: 'uploaded' },
    'elevations': { file: { name: 'Building_Elevations.pdf', size: 3200000 }, status: 'uploaded' },
    'sections': { file: null, status: 'pending' },
    'structural': { file: { name: 'Structural_Engineering.pdf', size: 5600000 }, status: 'uploaded' },
    'structural-calcs': { file: null, status: 'pending' },
    'geotech': { file: { name: 'Geotech_Report_2024.pdf', size: 8900000 }, status: 'uploaded' },
    'specs': { file: null, status: 'pending' },
    'branz': { file: null, status: 'pending' },
    'energy': { file: { name: 'H1_Compliance_Calcs.pdf', size: 1200000 }, status: 'uploaded' },
    'fire': { file: null, status: 'optional' },
    'drainage': { file: null, status: 'pending' },
  });

  const docs = [
    { id: 'ba2', name: 'Building Consent Application Form (BA2)' },
    { id: 'ownership', name: 'Certificate of Title' },
    { id: 'site-plan', name: 'Site Plan' },
    { id: 'floor-plans', name: 'Floor Plans' },
    { id: 'elevations', name: 'Building Elevations' },
    { id: 'sections', name: 'Cross Sections' },
    { id: 'structural', name: 'Structural Engineering Plans' },
    { id: 'structural-calcs', name: 'Structural Calculations' },
    { id: 'geotech', name: 'Geotechnical Report' },
    { id: 'specs', name: 'Building Specifications' },
    { id: 'branz', name: 'Product Specifications' },
    { id: 'energy', name: 'Energy Compliance (H1)' },
    { id: 'fire', name: 'Fire Safety Schedule' },
    { id: 'drainage', name: 'Drainage Plans' },
  ];

  const uploadedCount = Object.values(uploads).filter(u => u.status === 'uploaded').length;
  const pendingCount = Object.values(uploads).filter(u => u.status === 'pending').length;

  const formatSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / 1048576).toFixed(1) + ' MB';
  };

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="bg-gradient-to-r from-slate-50 to-white px-6 py-4 border-b border-slate-200">
          <h2 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
            <Upload className="w-5 h-5 text-violet-600" />
            Upload Documents
          </h2>
          <p className="text-sm text-slate-500 mt-1">Upload all required documents for verification</p>
        </div>

        <div className="p-6 space-y-6">
          {/* Progress summary */}
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <div className="flex justify-between text-sm mb-2">
                <span className="text-slate-600">Upload Progress</span>
                <span className="font-medium text-emerald-600">{uploadedCount} of {docs.length - 1} required</span>
              </div>
              <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-gradient-to-r from-emerald-500 to-teal-500 transition-all"
                  style={{ width: `${(uploadedCount / (docs.length - 1)) * 100}%` }}
                />
              </div>
            </div>
            <div className="flex gap-2">
              <span className="px-3 py-1 bg-emerald-100 text-emerald-700 rounded-full text-sm font-medium">
                {uploadedCount} uploaded
              </span>
              <span className="px-3 py-1 bg-amber-100 text-amber-700 rounded-full text-sm font-medium">
                {pendingCount} pending
              </span>
            </div>
          </div>

          {/* Bulk upload zone */}
          <div className="border-2 border-dashed border-slate-300 rounded-xl p-8 text-center hover:border-emerald-400 hover:bg-emerald-50/30 transition-all cursor-pointer">
            <Upload className="w-12 h-12 text-slate-400 mx-auto mb-3" />
            <p className="text-slate-600 font-medium">Drag and drop files here</p>
            <p className="text-sm text-slate-400 mt-1">or click to browse</p>
            <p className="text-xs text-slate-400 mt-3">Supported: PDF, DWG, DXF • Max 50MB per file</p>
          </div>

          {/* Document list */}
          <div className="space-y-2">
            {docs.map(doc => {
              const upload = uploads[doc.id];
              const isUploaded = upload.status === 'uploaded';
              const isPending = upload.status === 'pending';
              const isOptional = upload.status === 'optional';

              return (
                <div key={doc.id} className={`
                  flex items-center justify-between p-4 rounded-xl border transition-all
                  ${isUploaded ? 'bg-emerald-50 border-emerald-200' : ''}
                  ${isPending ? 'bg-amber-50 border-amber-200' : ''}
                  ${isOptional ? 'bg-slate-50 border-slate-200' : ''}
                `}>
                  <div className="flex items-center gap-3">
                    <div className={`
                      w-10 h-10 rounded-lg flex items-center justify-center
                      ${isUploaded ? 'bg-emerald-100' : ''}
                      ${isPending ? 'bg-amber-100' : ''}
                      ${isOptional ? 'bg-slate-100' : ''}
                    `}>
                      {isUploaded ? <CheckCircle2 className="w-5 h-5 text-emerald-600" /> : null}
                      {isPending ? <FileWarning className="w-5 h-5 text-amber-600" /> : null}
                      {isOptional ? <FileText className="w-5 h-5 text-slate-400" /> : null}
                    </div>
                    <div>
                      <p className="text-sm font-medium text-slate-700">{doc.name}</p>
                      {upload.file && (
                        <p className="text-xs text-slate-500">{upload.file.name} • {formatSize(upload.file.size)}</p>
                      )}
                      {isPending && <p className="text-xs text-amber-600">Required - not yet uploaded</p>}
                      {isOptional && <p className="text-xs text-slate-400">Optional</p>}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {isUploaded && (
                      <>
                        <button className="p-2 text-slate-400 hover:text-slate-600 transition-colors">
                          <Eye className="w-4 h-4" />
                        </button>
                        <button className="p-2 text-slate-400 hover:text-rose-500 transition-colors">
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </>
                    )}
                    {(isPending || isOptional) && (
                      <button className="px-4 py-2 bg-white border border-slate-300 rounded-lg text-sm font-medium text-slate-600 hover:bg-slate-50 transition-colors">
                        Upload
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="flex justify-between items-center">
        <div className="flex items-center gap-3">
          <button onClick={onBack} className="flex items-center gap-2 px-5 py-2.5 text-slate-600 hover:text-slate-800 transition-colors">
            <ChevronLeft className="w-5 h-5" />
            Back
          </button>
          <button className="flex items-center gap-2 px-5 py-2.5 text-slate-600 hover:text-slate-800 transition-colors">
            <Save className="w-4 h-4" />
            Save Draft
          </button>
        </div>
        <button
          onClick={onNext}
          className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-emerald-600 to-teal-600 text-white rounded-xl font-medium hover:from-emerald-700 hover:to-teal-700 transition-all shadow-lg shadow-emerald-500/20"
        >
          Verify Documents
          <ChevronRight className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
};

// ===== STEP 6: VERIFICATION =====
const Step6Verification = ({ data, onNext, onBack }) => {
  const [verifying, setVerifying] = useState(true);
  const [results, setResults] = useState(null);

  useEffect(() => {
    setTimeout(() => {
      setVerifying(false);
      setResults({
        passed: 10,
        warnings: 2,
        errors: 2,
        items: [
          { doc: 'Site Plan', status: 'pass', message: 'Scale verified, boundaries clear' },
          { doc: 'Floor Plans', status: 'pass', message: 'All levels present, dimensions complete' },
          { doc: 'Building Elevations', status: 'pass', message: 'All faces documented' },
          { doc: 'Structural Engineering', status: 'pass', message: 'PS1 certification present' },
          { doc: 'Geotech Report', status: 'pass', message: 'Foundation recommendations included' },
          { doc: 'H1 Energy Compliance', status: 'pass', message: 'Calculations verified' },
          { doc: 'BA2 Form', status: 'error', message: 'Document not uploaded' },
          { doc: 'Certificate of Title', status: 'error', message: 'Document not uploaded' },
          { doc: 'Cross Sections', status: 'warning', message: 'Missing height to boundary notation' },
          { doc: 'Structural Calculations', status: 'warning', message: 'Wind zone confirmation needed' },
        ]
      });
    }, 2500);
  }, []);

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="bg-gradient-to-r from-slate-50 to-white px-6 py-4 border-b border-slate-200">
          <h2 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
            <FileCheck className="w-5 h-5 text-indigo-600" />
            Document Verification
          </h2>
          <p className="text-sm text-slate-500 mt-1">Checking completeness, formats, and key data</p>
        </div>

        <div className="p-6">
          {verifying ? (
            <div className="py-12 text-center">
              <div className="w-16 h-16 mx-auto mb-4 relative">
                <div className="absolute inset-0 border-4 border-slate-200 rounded-full"></div>
                <div className="absolute inset-0 border-4 border-emerald-500 rounded-full animate-spin border-t-transparent"></div>
                <FileCheck className="w-6 h-6 text-emerald-600 absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />
              </div>
              <p className="text-slate-600 font-medium">Verifying documents...</p>
              <p className="text-sm text-slate-400 mt-1">Checking formats, completeness, and compliance data</p>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Summary cards */}
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-emerald-50 rounded-xl p-4 border border-emerald-100">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-emerald-100 rounded-lg flex items-center justify-center">
                      <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                    </div>
                    <div>
                      <div className="text-2xl font-bold text-emerald-700">{results.passed}</div>
                      <div className="text-sm text-emerald-600">Passed</div>
                    </div>
                  </div>
                </div>
                <div className="bg-amber-50 rounded-xl p-4 border border-amber-100">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-amber-100 rounded-lg flex items-center justify-center">
                      <AlertTriangle className="w-5 h-5 text-amber-600" />
                    </div>
                    <div>
                      <div className="text-2xl font-bold text-amber-700">{results.warnings}</div>
                      <div className="text-sm text-amber-600">Warnings</div>
                    </div>
                  </div>
                </div>
                <div className="bg-rose-50 rounded-xl p-4 border border-rose-100">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-rose-100 rounded-lg flex items-center justify-center">
                      <XCircle className="w-5 h-5 text-rose-600" />
                    </div>
                    <div>
                      <div className="text-2xl font-bold text-rose-700">{results.errors}</div>
                      <div className="text-sm text-rose-600">Issues</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Results list */}
              <div className="space-y-2">
                {results.items.map((item, i) => (
                  <div key={i} className={`
                    flex items-center justify-between p-4 rounded-xl border
                    ${item.status === 'pass' ? 'bg-emerald-50/50 border-emerald-100' : ''}
                    ${item.status === 'warning' ? 'bg-amber-50/50 border-amber-100' : ''}
                    ${item.status === 'error' ? 'bg-rose-50/50 border-rose-100' : ''}
                  `}>
                    <div className="flex items-center gap-3">
                      {item.status === 'pass' && <CheckCircle2 className="w-5 h-5 text-emerald-600" />}
                      {item.status === 'warning' && <AlertTriangle className="w-5 h-5 text-amber-600" />}
                      {item.status === 'error' && <XCircle className="w-5 h-5 text-rose-600" />}
                      <div>
                        <p className="font-medium text-slate-700">{item.doc}</p>
                        <p className="text-sm text-slate-500">{item.message}</p>
                      </div>
                    </div>
                    {item.status !== 'pass' && (
                      <button className="px-4 py-2 bg-white border border-slate-300 rounded-lg text-sm font-medium text-slate-600 hover:bg-slate-50">
                        {item.status === 'error' ? 'Upload' : 'Review'}
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Actions */}
      <div className="flex justify-between items-center">
        <button onClick={onBack} className="flex items-center gap-2 px-5 py-2.5 text-slate-600 hover:text-slate-800 transition-colors">
          <ChevronLeft className="w-5 h-5" />
          Back to Upload
        </button>
        <button
          onClick={onNext}
          disabled={verifying}
          className={`flex items-center gap-2 px-6 py-3 rounded-xl font-medium transition-all shadow-lg ${
            verifying 
              ? 'bg-slate-200 text-slate-400 cursor-not-allowed' 
              : 'bg-gradient-to-r from-emerald-600 to-teal-600 text-white hover:from-emerald-700 hover:to-teal-700 shadow-emerald-500/20'
          }`}
        >
          Continue
          <ChevronRight className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
};

// ===== STEP 7: RESOLVE ISSUES =====
const Step7ResolveIssues = ({ data, onNext, onBack }) => {
  const [justifications, setJustifications] = useState({});

  const issues = [
    { id: 'ba2', type: 'error', doc: 'BA2 Application Form', message: 'Document not uploaded' },
    { id: 'title', type: 'error', doc: 'Certificate of Title', message: 'Document not uploaded' },
    { id: 'sections', type: 'warning', doc: 'Cross Sections', message: 'Missing height to boundary notation' },
    { id: 'wind', type: 'warning', doc: 'Structural Calculations', message: 'Wind zone confirmation needed' },
  ];

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="bg-gradient-to-r from-slate-50 to-white px-6 py-4 border-b border-slate-200">
          <h2 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-amber-500" />
            Resolve Outstanding Items
          </h2>
          <p className="text-sm text-slate-500 mt-1">Upload missing documents or provide justification</p>
        </div>

        <div className="p-6 space-y-6">
          {/* Warning banner */}
          <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="font-semibold text-amber-800">Action Required</h3>
              <p className="text-sm text-amber-700 mt-1">
                Please upload missing documents or provide justification. Submitting with unresolved issues may result in a Request for Information (RFI) from the council.
              </p>
            </div>
          </div>

          {/* Issues list */}
          <div className="space-y-4">
            {issues.map(issue => (
              <div key={issue.id} className={`
                rounded-xl border-2 p-5
                ${issue.type === 'error' ? 'border-rose-200 bg-rose-50/30' : 'border-amber-200 bg-amber-50/30'}
              `}>
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    {issue.type === 'error' ? (
                      <XCircle className="w-5 h-5 text-rose-600" />
                    ) : (
                      <AlertTriangle className="w-5 h-5 text-amber-600" />
                    )}
                    <div>
                      <h4 className="font-semibold text-slate-800">{issue.doc}</h4>
                      <p className="text-sm text-slate-500">{issue.message}</p>
                    </div>
                  </div>
                  <span className={`
                    px-3 py-1 rounded-full text-xs font-medium
                    ${issue.type === 'error' ? 'bg-rose-100 text-rose-700' : 'bg-amber-100 text-amber-700'}
                  `}>
                    {issue.type === 'error' ? 'Missing' : 'Warning'}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <button className="flex items-center justify-center gap-2 px-4 py-3 bg-white border border-slate-300 rounded-xl text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors">
                    <Upload className="w-4 h-4" />
                    Upload Document
                  </button>
                  <div>
                    <textarea
                      placeholder="Or provide justification/explanation..."
                      value={justifications[issue.id] || ''}
                      onChange={(e) => setJustifications(prev => ({ ...prev, [issue.id]: e.target.value }))}
                      rows={2}
                      className="w-full px-3 py-2 text-sm rounded-xl border border-slate-300 focus:ring-2 focus:ring-emerald-500 resize-none"
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Declaration */}
          <div className="bg-slate-50 rounded-xl p-5 border border-slate-200">
            <label className="flex items-start gap-3 cursor-pointer">
              <input type="checkbox" className="w-5 h-5 rounded border-slate-300 text-emerald-600 mt-0.5" />
              <div>
                <p className="font-medium text-slate-800">I acknowledge the outstanding items</p>
                <p className="text-sm text-slate-500 mt-1">
                  I understand that submitting this application with unresolved items may result in a Request for Information (RFI) 
                  and potential delays in processing.
                </p>
              </div>
            </label>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="flex justify-between items-center">
        <div className="flex items-center gap-3">
          <button onClick={onBack} className="flex items-center gap-2 px-5 py-2.5 text-slate-600 hover:text-slate-800 transition-colors">
            <ChevronLeft className="w-5 h-5" />
            Back
          </button>
          <button className="flex items-center gap-2 px-5 py-2.5 text-slate-600 hover:text-slate-800 transition-colors">
            <Save className="w-4 h-4" />
            Save Draft
          </button>
        </div>
        <button
          onClick={onNext}
          className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-emerald-600 to-teal-600 text-white rounded-xl font-medium hover:from-emerald-700 hover:to-teal-700 transition-all shadow-lg shadow-emerald-500/20"
        >
          Generate Summary
          <ChevronRight className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
};

// ===== STEP 8: VALIDATION SUMMARY =====
const Step8ValidationSummary = ({ data, onNext, onBack }) => {
  const hasWarnings = true; // Demo state

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="bg-gradient-to-r from-slate-50 to-white px-6 py-4 border-b border-slate-200">
          <h2 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
            <FileCheck className="w-5 h-5 text-emerald-600" />
            Validation Summary
          </h2>
          <p className="text-sm text-slate-500 mt-1">Review your complete application package</p>
        </div>

        <div className="p-6 space-y-6">
          {/* Status banner */}
          {hasWarnings ? (
            <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex items-start gap-3">
              <AlertTriangle className="w-6 h-6 text-amber-600 flex-shrink-0" />
              <div>
                <h3 className="font-semibold text-amber-800">Ready with Warnings</h3>
                <p className="text-sm text-amber-700 mt-1">
                  Your application can be submitted but may receive a Request for Information (RFI) due to unresolved items.
                </p>
              </div>
            </div>
          ) : (
            <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4 flex items-start gap-3">
              <CheckCircle2 className="w-6 h-6 text-emerald-600 flex-shrink-0" />
              <div>
                <h3 className="font-semibold text-emerald-800">Validation Complete</h3>
                <p className="text-sm text-emerald-700 mt-1">
                  All checks have passed. Your application package is ready for submission.
                </p>
              </div>
            </div>
          )}

          {/* Project summary */}
          <div className="bg-slate-50 rounded-xl p-5">
            <h3 className="font-semibold text-slate-800 mb-4">Project Summary</h3>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-slate-500">Project:</span>
                <p className="font-medium text-slate-800">{data.projectOverview?.projectName || 'Smith Family Residence'}</p>
              </div>
              <div>
                <span className="text-slate-500">Type:</span>
                <p className="font-medium text-slate-800">New 3-Bedroom Dwelling</p>
              </div>
              <div>
                <span className="text-slate-500">Address:</span>
                <p className="font-medium text-slate-800">{data.projectDetails?.address || '42 Greenview Lane, Auckland'}</p>
              </div>
              <div>
                <span className="text-slate-500">Reference:</span>
                <p className="font-medium text-slate-800">CC-2025-00847</p>
              </div>
            </div>
          </div>

          {/* Validation results */}
          <div className="grid grid-cols-4 gap-4">
            <div className="bg-emerald-50 rounded-xl p-4 text-center border border-emerald-100">
              <div className="text-2xl font-bold text-emerald-700">10</div>
              <div className="text-xs text-emerald-600">Documents Verified</div>
            </div>
            <div className="bg-amber-50 rounded-xl p-4 text-center border border-amber-100">
              <div className="text-2xl font-bold text-amber-700">2</div>
              <div className="text-xs text-amber-600">Warnings</div>
            </div>
            <div className="bg-blue-50 rounded-xl p-4 text-center border border-blue-100">
              <div className="text-2xl font-bold text-blue-700">6</div>
              <div className="text-xs text-blue-600">Compliance Areas</div>
            </div>
            <div className="bg-violet-50 rounded-xl p-4 text-center border border-violet-100">
              <div className="text-2xl font-bold text-violet-700">~20</div>
              <div className="text-xs text-violet-600">Est. Days</div>
            </div>
          </div>

          {/* Document checklist */}
          <div>
            <h3 className="font-semibold text-slate-800 mb-3">Included Documents</h3>
            <div className="grid grid-cols-2 gap-2">
              {/* Form 2 - Auto-populated by AI */}
              <div className="flex items-center gap-2 text-sm bg-gradient-to-r from-violet-50 to-purple-50 rounded-lg p-2 border border-violet-200">
                <div className="flex items-center gap-2 flex-1">
                  <CheckCircle2 className="w-4 h-4 text-violet-500" />
                  <span className="text-slate-700">Form 2</span>
                </div>
                <span className="text-xs bg-violet-100 text-violet-700 px-2 py-0.5 rounded-full flex items-center gap-1">
                  <Zap className="w-3 h-3" />
                  CompliCheckAI filled
                </span>
              </div>
              {['Site Plan', 'Floor Plans', 'Elevations', 'Structural Plans', 'Geotech Report', 'H1 Compliance', 'Specifications', 'Drainage Plans'].map((doc, i) => (
                <div key={i} className="flex items-center gap-2 text-sm text-slate-600 bg-slate-50 rounded-lg p-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                  {doc}
                </div>
              ))}
            </div>
          </div>

          {/* Download options */}
          <div className="flex items-center gap-3 pt-4 border-t border-slate-200">
            <button className="flex items-center gap-2 px-4 py-2 bg-slate-100 rounded-lg text-sm font-medium text-slate-700 hover:bg-slate-200 transition-colors">
              <Download className="w-4 h-4" />
              Download Report (PDF)
            </button>
            <button className="flex items-center gap-2 px-4 py-2 bg-slate-100 rounded-lg text-sm font-medium text-slate-700 hover:bg-slate-200 transition-colors">
              <Eye className="w-4 h-4" />
              Preview Package
            </button>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="flex justify-between items-center">
        <button onClick={onBack} className="flex items-center gap-2 px-5 py-2.5 text-slate-600 hover:text-slate-800 transition-colors">
          <ChevronLeft className="w-5 h-5" />
          Back
        </button>
        <button
          onClick={onNext}
          className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-emerald-600 to-teal-600 text-white rounded-xl font-medium hover:from-emerald-700 hover:to-teal-700 transition-all shadow-lg shadow-emerald-500/20"
        >
          Proceed to Submit
          <ChevronRight className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
};

// ===== STEP 9: SUBMIT TO COUNCIL =====
const Step9SubmitToCouncil = ({ data, onBack }) => {
  const [agreed, setAgreed] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = () => {
    setSubmitting(true);
    setTimeout(() => {
      setSubmitting(false);
      setSubmitted(true);
    }, 3000);
  };

  if (submitted) {
    return (
      <div className="space-y-6">
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
          <div className="p-12 text-center">
            <div className="w-20 h-20 mx-auto mb-6 bg-gradient-to-br from-emerald-500 to-teal-500 rounded-full flex items-center justify-center shadow-lg shadow-emerald-500/30">
              <CheckCircle2 className="w-10 h-10 text-white" />
            </div>
            <h2 className="text-2xl font-bold text-slate-800 mb-2">Successfully Submitted!</h2>
            <p className="text-slate-500 max-w-md mx-auto">
              Your building consent application has been submitted to Auckland Council via the API integration.
            </p>

            <div className="bg-slate-50 rounded-xl p-6 mt-8 max-w-md mx-auto">
              <div className="space-y-3 text-left">
                <div className="flex justify-between">
                  <span className="text-slate-500">Submission Reference:</span>
                  <span className="font-mono font-semibold text-slate-800">BC-2025-00847</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Submitted:</span>
                  <span className="font-medium text-slate-800">{new Date().toLocaleDateString()}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Status:</span>
                  <span className="px-2 py-1 bg-emerald-100 text-emerald-700 rounded-full text-xs font-medium">Received</span>
                </div>
              </div>
            </div>

            <div className="flex items-center justify-center gap-4 mt-8">
              <button className="flex items-center gap-2 px-5 py-2.5 bg-slate-100 rounded-xl text-slate-700 font-medium hover:bg-slate-200 transition-colors">
                <Download className="w-4 h-4" />
                Download Confirmation
              </button>
              <button className="flex items-center gap-2 px-5 py-2.5 bg-emerald-600 text-white rounded-xl font-medium hover:bg-emerald-700 transition-colors">
                <Home className="w-4 h-4" />
                Return to Dashboard
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="bg-gradient-to-r from-slate-50 to-white px-6 py-4 border-b border-slate-200">
          <h2 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
            <Send className="w-5 h-5 text-emerald-600" />
            Submit to Council
          </h2>
          <p className="text-sm text-slate-500 mt-1">Final review and submission via API integration</p>
        </div>

        <div className="p-6 space-y-6">
          {/* Warning about RFI */}
          <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="font-semibold text-amber-800">RFI Warning</h3>
              <p className="text-sm text-amber-700 mt-1">
                Your application contains unresolved items. The council may issue a Request for Information (RFI), 
                which could delay processing. You have provided justification for these items.
              </p>
            </div>
          </div>

          {/* Submission details */}
          <div className="bg-slate-50 rounded-xl p-5">
            <h3 className="font-semibold text-slate-800 mb-4">Submission Package</h3>
            <div className="space-y-3 text-sm">
              <div className="flex items-center justify-between py-2 border-b border-slate-200">
                <span className="text-slate-600">Building Consent Form 2 (BA2)</span>
                <CheckCircle2 className="w-4 h-4 text-emerald-500" />
              </div>
              <div className="flex items-center justify-between py-2 border-b border-slate-200">
                <span className="text-slate-600">All attached documents (10 files)</span>
                <CheckCircle2 className="w-4 h-4 text-emerald-500" />
              </div>
              <div className="flex items-center justify-between py-2 border-b border-slate-200">
                <span className="text-slate-600">Validation report</span>
                <CheckCircle2 className="w-4 h-4 text-emerald-500" />
              </div>
              <div className="flex items-center justify-between py-2">
                <span className="text-slate-600">Applicant declarations</span>
                <CheckCircle2 className="w-4 h-4 text-emerald-500" />
              </div>
            </div>
          </div>

          {/* Notifications */}
          <div className="bg-blue-50 rounded-xl p-4 border border-blue-100">
            <h4 className="font-medium text-blue-800 mb-2">Upon Submission</h4>
            <ul className="text-sm text-blue-700 space-y-1">
              <li>• Internal confirmation email sent to you</li>
              <li>• Report sent to Building Control Officer (BCO)</li>
              <li>• Application lodged in council system via API</li>
              <li>• Traceability records stored</li>
            </ul>
          </div>

          {/* Final declaration */}
          <div className="border-2 border-slate-200 rounded-xl p-5">
            <label className="flex items-start gap-3 cursor-pointer">
              <input 
                type="checkbox" 
                checked={agreed}
                onChange={(e) => setAgreed(e.target.checked)}
                className="w-5 h-5 rounded border-slate-300 text-emerald-600 mt-0.5" 
              />
              <div>
                <p className="font-medium text-slate-800">Declaration</p>
                <p className="text-sm text-slate-500 mt-1">
                  I declare that the information provided in this application is true and correct. 
                  I understand that submitting false information may result in rejection or revocation of any consent granted.
                  I acknowledge that this application may receive an RFI due to outstanding items.
                </p>
              </div>
            </label>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="flex justify-between items-center">
        <button onClick={onBack} className="flex items-center gap-2 px-5 py-2.5 text-slate-600 hover:text-slate-800 transition-colors">
          <ChevronLeft className="w-5 h-5" />
          Back
        </button>
        <button
          onClick={handleSubmit}
          disabled={!agreed || submitting}
          className={`flex items-center gap-2 px-8 py-3 rounded-xl font-medium transition-all shadow-lg ${
            !agreed || submitting
              ? 'bg-slate-200 text-slate-400 cursor-not-allowed' 
              : 'bg-gradient-to-r from-emerald-600 to-teal-600 text-white hover:from-emerald-700 hover:to-teal-700 shadow-emerald-500/20'
          }`}
        >
          {submitting ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Submitting...
            </>
          ) : (
            <>
              <Send className="w-5 h-5" />
              Submit to Council
            </>
          )}
        </button>
      </div>
    </div>
  );
};

// ===== MAIN APP =====
export default function CompliCheckAI() {
  const [currentStep, setCurrentStep] = useState(1);
  const [data, setData] = useState({});

  const steps = [
    { id: 1, label: 'Overview' },
    { id: 2, label: 'Details' },
    { id: 3, label: 'Analysis' },
    { id: 4, label: 'Requirements' },
    { id: 5, label: 'Upload' },
    { id: 6, label: 'Verification' },
    { id: 7, label: 'Resolve' },
    { id: 8, label: 'Summary' },
    { id: 9, label: 'Submit' },
  ];

  const renderStep = () => {
    switch (currentStep) {
      case 1:
        return <Step1ProjectOverview data={data} setData={setData} onNext={() => setCurrentStep(2)} />;
      case 2:
        return <Step2ProjectDetails data={data} setData={setData} onNext={() => setCurrentStep(3)} onBack={() => setCurrentStep(1)} />;
      case 3:
        return <Step3SystemAnalysis data={data} onNext={() => setCurrentStep(4)} onBack={() => setCurrentStep(2)} />;
      case 4:
        return <Step4RequiredDocuments data={data} setData={setData} onNext={() => setCurrentStep(5)} onBack={() => setCurrentStep(3)} />;
      case 5:
        return <Step5UploadDocuments data={data} setData={setData} onNext={() => setCurrentStep(6)} onBack={() => setCurrentStep(4)} />;
      case 6:
        return <Step6Verification data={data} onNext={() => setCurrentStep(7)} onBack={() => setCurrentStep(5)} />;
      case 7:
        return <Step7ResolveIssues data={data} onNext={() => setCurrentStep(8)} onBack={() => setCurrentStep(6)} />;
      case 8:
        return <Step8ValidationSummary data={data} onNext={() => setCurrentStep(9)} onBack={() => setCurrentStep(7)} />;
      case 9:
        return <Step9SubmitToCouncil data={data} onBack={() => setCurrentStep(8)} />;
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-100 via-slate-50 to-white flex flex-col" style={{ fontFamily: "'Inter', system-ui, sans-serif" }}>
      <Header currentStep={currentStep} />
      
      <main className="flex-1 max-w-5xl mx-auto w-full px-6 py-8">
        <ProgressStepper currentStep={currentStep} steps={steps} />
        {renderStep()}
      </main>

      <Footer />
    </div>
  );
}
