export default function PricingPage() {
  const plans = [
    {
      title: "Retail Investor",
      price: "$99/mo",
      features: ["3 signals per month", "Weekly contrarian newsletter"],
      cta: "Subscribe Now",
    },
    {
      title: "Hedge Fund Light",
      price: "$2,000/mo",
      features: ["1 signal per day (~22/mo)", "Dashboard access (commodities + cities)", "WhatsApp alerts via Twilio"],
      cta: "Upgrade to Light",
      featured: true,
    },
    {
      title: "Hedge Fund Full",
      price: "$15,000/mo",
      features: [
        "Unlimited real-time signals",
        "Dashboard + War-Room Mode",
        "Scenario Playbooks",
        "JSON API Feed",
        "WhatsApp distribution (Twilio)",
      ],
      cta: "Contact Sales",
    },
  ]

  return (
    <div className="min-h-screen bg-white py-16">
      <div className="max-w-7xl mx-auto px-4">
        <div className="text-center mb-16">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">Pricing Plans</h1>
          <p className="text-xl text-gray-600">Intelligence signals for contrarian investors</p>
        </div>

        <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
          {plans.map((plan) => (
            <div
              key={plan.title}
              className={`p-8 rounded-xl border ${
                plan.featured ? "border-blue-500 shadow-lg shadow-blue-500/10 bg-blue-50" : "border-gray-200 bg-white"
              } hover:shadow-xl transition-shadow`}
            >
              {plan.featured && (
                <div className="text-center mb-4">
                  <span className="bg-blue-600 text-white px-3 py-1 rounded-full text-sm font-medium">
                    Most Popular
                  </span>
                </div>
              )}

              <h2 className="text-2xl font-bold mb-2 text-gray-900">{plan.title}</h2>
              <p className="text-3xl font-extrabold text-blue-600 mb-6">{plan.price}</p>

              <ul className="space-y-3 mb-8">
                {plan.features.map((feature) => (
                  <li key={feature} className="flex items-start text-gray-700">
                    <span className="text-green-500 mr-3 mt-0.5">✓</span>
                    {feature}
                  </li>
                ))}
              </ul>

              <button
                className={`w-full py-3 rounded-lg font-semibold transition-colors ${
                  plan.featured
                    ? "bg-blue-600 text-white hover:bg-blue-700"
                    : "bg-gray-100 text-gray-900 hover:bg-gray-200 border border-gray-300"
                }`}
              >
                {plan.cta}
              </button>
            </div>
          ))}
        </div>

        <div className="text-center mt-16">
          <p className="text-gray-600 text-sm">
            All plans include intelligence signals only. We provide structured signals and anomalies from public data
            sources. We do not provide investment advice or execution services.
          </p>
        </div>
      </div>
    </div>
  )
}
