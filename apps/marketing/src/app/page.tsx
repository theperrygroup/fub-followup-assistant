import { CheckIcon, ChatBubbleLeftRightIcon, RocketLaunchIcon, ShieldCheckIcon } from '@heroicons/react/24/outline'
import Link from 'next/link'

const features = [
  {
    name: 'AI-Powered Suggestions',
    description: 'Get personalized follow-up recommendations based on lead data and real estate best practices.',
    icon: ChatBubbleLeftRightIcon,
  },
  {
    name: 'Automatic Note Creation',
    description: 'One-click note creation directly in Follow Up Boss from AI suggestions.',
    icon: RocketLaunchIcon,
  },
  {
    name: 'Secure Integration',
    description: 'HMAC-verified iframe integration with Follow Up Boss for maximum security.',
    icon: ShieldCheckIcon,
  },
]

const pricing = [
  {
    name: 'Starter',
    price: '$29',
    description: 'Perfect for individual agents',
    features: [
      '100 AI conversations per month',
      'Basic follow-up suggestions',
      'Note creation integration',
      'Email support'
    ]
  },
  {
    name: 'Professional',
    price: '$59',
    description: 'For growing teams',
    features: [
      '500 AI conversations per month',
      'Advanced follow-up strategies',
      'Priority support',
      'Team analytics',
      'Custom templates'
    ],
    popular: true
  },
  {
    name: 'Enterprise',
    price: '$99',
    description: 'For large brokerages',
    features: [
      'Unlimited AI conversations',
      'Custom AI training',
      'White-label options',
      'Dedicated support',
      'API access'
    ]
  }
]

export default function HomePage() {
  return (
    <div className="bg-white">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="container-max-width">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-brand-600 rounded-lg flex items-center justify-center">
                <ChatBubbleLeftRightIcon className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold text-gray-900">FUB Assistant</span>
            </div>
            
            <nav className="hidden md:flex space-x-8">
              <a href="#features" className="text-gray-600 hover:text-gray-900">Features</a>
              <a href="#pricing" className="text-gray-600 hover:text-gray-900">Pricing</a>
              <a href="#contact" className="text-gray-600 hover:text-gray-900">Contact</a>
            </nav>
            
            <div className="flex items-center space-x-4">
              <Link href="/auth/login" className="text-gray-600 hover:text-gray-900">
                Sign In
              </Link>
              <Link href="/auth/signup" className="btn-primary">
                Get Started
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="section-padding bg-gradient-to-br from-brand-50 to-white">
        <div className="container-max-width">
          <div className="text-center">
            <h1 className="text-5xl md:text-6xl font-bold text-gray-900 mb-6">
              Supercharge Your
              <span className="text-brand-600"> Follow Up Boss </span>
              with AI
            </h1>
            <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
              Get intelligent follow-up suggestions, automated note creation, and personalized 
              real estate advice directly in your Follow Up Boss CRM.
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link href="/auth/signup" className="btn-primary">
                Start Free Trial
              </Link>
              <button className="btn-secondary">
                Watch Demo
              </button>
            </div>
            
            <p className="text-sm text-gray-500 mt-4">
              14-day free trial • No credit card required
            </p>
          </div>
          
          {/* Hero Image/Demo */}
          <div className="mt-16">
            <div className="bg-white rounded-xl shadow-2xl p-8 max-w-4xl mx-auto">
              <div className="bg-gray-100 rounded-lg p-6">
                <div className="flex items-center space-x-2 mb-4">
                  <div className="w-3 h-3 bg-red-400 rounded-full"></div>
                  <div className="w-3 h-3 bg-yellow-400 rounded-full"></div>
                  <div className="w-3 h-3 bg-green-400 rounded-full"></div>
                  <span className="text-sm text-gray-500 ml-4">Follow Up Boss - Lead Profile</span>
                </div>
                <div className="bg-white rounded-lg p-4 border-l-4 border-brand-500">
                  <h3 className="font-semibold text-gray-800 mb-2">FUB Follow-up Assistant</h3>
                  <p className="text-gray-600 text-sm">
                    "Based on Sarah's recent property search and budget, I recommend reaching out with 
                    similar listings in the Brookhaven area. She showed strong interest in homes with 
                    modern kitchens and good school districts."
                  </p>
                  <button className="mt-2 text-xs bg-brand-100 text-brand-700 px-3 py-1 rounded-full">
                    Create Note in FUB
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="section-padding">
        <div className="container-max-width">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">
              Everything you need to close more deals
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Our AI assistant integrates seamlessly with Follow Up Boss to provide 
              intelligent insights and automate your follow-up process.
            </p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-8">
            {features.map((feature) => (
              <div key={feature.name} className="text-center">
                <div className="w-16 h-16 bg-brand-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                  <feature.icon className="w-8 h-8 text-brand-600" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">{feature.name}</h3>
                <p className="text-gray-600">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="section-padding bg-gray-50">
        <div className="container-max-width">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">
              Simple, transparent pricing
            </h2>
            <p className="text-xl text-gray-600">
              Choose the plan that fits your business
            </p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-8">
            {pricing.map((plan) => (
              <div key={plan.name} className={`bg-white rounded-xl p-8 relative ${
                plan.popular ? 'ring-2 ring-brand-500 shadow-lg' : 'shadow-md'
              }`}>
                {plan.popular && (
                  <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                    <span className="bg-brand-500 text-white px-4 py-1 rounded-full text-sm font-medium">
                      Most Popular
                    </span>
                  </div>
                )}
                
                <div className="text-center mb-6">
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">{plan.name}</h3>
                  <div className="flex items-baseline justify-center">
                    <span className="text-4xl font-bold text-gray-900">{plan.price}</span>
                    <span className="text-gray-500 ml-1">/month</span>
                  </div>
                  <p className="text-gray-600 mt-2">{plan.description}</p>
                </div>
                
                <ul className="space-y-3 mb-8">
                  {plan.features.map((feature) => (
                    <li key={feature} className="flex items-center">
                      <CheckIcon className="w-5 h-5 text-green-500 mr-3" />
                      <span className="text-gray-700">{feature}</span>
                    </li>
                  ))}
                </ul>
                
                <Link 
                  href={`/auth/signup?plan=${plan.name.toLowerCase()}`}
                  className={`block w-full text-center py-3 rounded-lg font-medium transition-colors ${
                    plan.popular 
                      ? 'bg-brand-600 text-white hover:bg-brand-700' 
                      : 'bg-gray-100 text-gray-900 hover:bg-gray-200'
                  }`}
                >
                  Get Started
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="section-padding bg-brand-600">
        <div className="container-max-width text-center">
          <h2 className="text-4xl font-bold text-white mb-4">
            Ready to boost your Follow Up Boss productivity?
          </h2>
          <p className="text-xl text-brand-100 mb-8 max-w-2xl mx-auto">
            Join hundreds of real estate professionals who are already using AI to close more deals.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/auth/signup" className="bg-white text-brand-600 px-8 py-4 rounded-lg font-medium hover:bg-gray-50 transition-colors">
              Start Free Trial
            </Link>
            <button className="bg-transparent text-white px-8 py-4 rounded-lg font-medium border border-white hover:bg-white hover:text-brand-600 transition-colors">
              Schedule Demo
            </button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white section-padding">
        <div className="container-max-width">
          <div className="grid md:grid-cols-4 gap-8">
            <div>
              <div className="flex items-center space-x-2 mb-4">
                <div className="w-8 h-8 bg-brand-600 rounded-lg flex items-center justify-center">
                  <ChatBubbleLeftRightIcon className="w-5 h-5 text-white" />
                </div>
                <span className="text-xl font-bold">FUB Assistant</span>
              </div>
              <p className="text-gray-400">
                AI-powered follow-up suggestions for Follow Up Boss CRM.
              </p>
            </div>
            
            <div>
              <h3 className="font-semibold mb-4">Product</h3>
              <ul className="space-y-2 text-gray-400">
                <li><a href="#features" className="hover:text-white">Features</a></li>
                <li><a href="#pricing" className="hover:text-white">Pricing</a></li>
                <li><a href="/integrations" className="hover:text-white">Integrations</a></li>
              </ul>
            </div>
            
            <div>
              <h3 className="font-semibold mb-4">Support</h3>
              <ul className="space-y-2 text-gray-400">
                <li><a href="/docs" className="hover:text-white">Documentation</a></li>
                <li><a href="/support" className="hover:text-white">Help Center</a></li>
                <li><a href="/contact" className="hover:text-white">Contact</a></li>
              </ul>
            </div>
            
            <div>
              <h3 className="font-semibold mb-4">Company</h3>
              <ul className="space-y-2 text-gray-400">
                <li><a href="/about" className="hover:text-white">About</a></li>
                <li><a href="/privacy" className="hover:text-white">Privacy</a></li>
                <li><a href="/terms" className="hover:text-white">Terms</a></li>
              </ul>
            </div>
          </div>
          
          <div className="border-t border-gray-800 mt-12 pt-8 text-center text-gray-400">
            <p>&copy; 2024 FUB Follow-up Assistant. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  )
} 