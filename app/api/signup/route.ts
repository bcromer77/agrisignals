import { type NextRequest, NextResponse } from "next/server"

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { email, firm, persona } = body

    console.log("[v0] Signup request:", { email, firm, persona })

    // Simulate processing delay
    await new Promise((resolve) => setTimeout(resolve, 1000))

    return NextResponse.json({
      success: true,
      message: "Signup successful",
      user: { email, firm, persona },
    })
  } catch (error) {
    console.error("[v0] Signup error:", error)
    return NextResponse.json({ success: false, message: "Signup failed" }, { status: 500 })
  }
}
