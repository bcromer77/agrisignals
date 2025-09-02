"use client"

import { useState } from "react"

export default function SignupPage() {
  const [form, setForm] = useState({ email: "", firm: "", persona: "Munger" })
  const [status, setStatus] = useState("")

  const handleChange = (e: any) => {
    setForm({ ...form, [e.target.name]: e.target.value })
  }

  const handleSubmit = async (e: any) => {
    e.preventDefault()
    setStatus("Submitting...")

    try {
      const res = await fetch("/api/signup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      })

      if (res.ok) {
        setStatus("Success! Redirecting to dashboard...")
        window.location.href = "/dashboard"
      } else {
        setStatus("Error submitting form. Try again.")
      }
    } catch {
      setStatus("Network error. Try again.")
    }
  }

  return (
    <div className="min-h-screen bg-white flex items-center justify-center">
      <div className="w-full max-w-md bg-white p-8 rounded-xl border border-gray-200 shadow-lg">
        <h1 className="text-3xl font-bold text-center mb-6 text-gray-900">Join Agrisignals PRISM</h1>
        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="email"
            name="email"
            placeholder="Email"
            className="w-full p-3 rounded-lg bg-gray-50 text-gray-900 border border-gray-300 focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
            value={form.email}
            onChange={handleChange}
            required
          />
          <input
            type="text"
            name="firm"
            placeholder="Firm / Organization"
            className="w-full p-3 rounded-lg bg-gray-50 text-gray-900 border border-gray-300 focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
            value={form.firm}
            onChange={handleChange}
          />
          <select
            name="persona"
            value={form.persona}
            onChange={handleChange}
            className="w-full p-3 rounded-lg bg-gray-50 text-gray-900 border border-gray-300 focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
          >
            <option value="Munger">🐢 Munger</option>
            <option value="Burry">💧 Burry</option>
            <option value="Axelrod">⚡ Axelrod</option>
          </select>
          <button
            type="submit"
            className="w-full py-3 rounded-lg bg-blue-600 text-white font-semibold hover:bg-blue-700 transition-colors"
          >
            Sign Up
          </button>
        </form>
        {status && <p className="mt-4 text-center text-sm text-gray-600">{status}</p>}
      </div>
    </div>
  )
}
