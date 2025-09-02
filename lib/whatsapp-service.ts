export interface WhatsAppMessage {
  to: string
  message: string
  signalId?: string
}

export class WhatsAppService {
  private twilioSid: string
  private twilioAuthToken: string
  private fromNumber: string

  constructor() {
    this.twilioSid = process.env.TWILIO_SID || ""
    this.twilioAuthToken = process.env.TWILIO_AUTH_TOKEN || ""
    this.fromNumber = process.env.TWILIO_WHATSAPP_NUMBER || "whatsapp:+14155238886"
  }

  async sendSignalAlert(signal: any, phoneNumber: string): Promise<boolean> {
    try {
      const message = this.formatSignalMessage(signal)
      return await this.sendMessage(phoneNumber, message)
    } catch (error) {
      console.error("[v0] WhatsApp send error:", error)
      return false
    }
  }

  private formatSignalMessage(signal: any): string {
    return `🚨 AGRISIGNALS ALERT
    
${signal.headline}

Confidence: ${signal.confidence}%
Category: ${signal.category}
Impact: ${signal.impact}

Provenance: ${signal.provenance}

⚠️ Intelligence signals only - We do not provide investment advice or execution services`
  }

  private async sendMessage(to: string, message: string): Promise<boolean> {
    // Mock implementation - replace with actual Twilio client
    console.log("[v0] WhatsApp message would be sent:", { to, message })
    return true
  }
}

export const whatsappService = new WhatsAppService()
