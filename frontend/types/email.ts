export type EmailFolder = "unified" | "unread" | "flagged" | "snoozed" | "archived" | "trash" | string

export type LetterCategory =
  | "official-government"
  | "financial-billing"
  | "banking-insurance"
  | "employment-hr"
  | "education-academic"
  | "healthcare-medical"
  | "legal-compliance"
  | "logistics-delivery"
  | "personal-social"
  | "real-estate-utilities"
  | "subscription-membership"
  | "marketing-promotions"
  | "travel-ticketing"
  | "nonprofit-ngo"
  | "miscellaneous"

export type ActionStatus = "require-action" | "action-done" | "no-action-needed"

export type EmailCategory = "work" | "personal" | "social" | "updates" | "promotions"

export interface SocialLink {
  platform: string
  url: string
  username?: string
}

export interface EmailSender {
  name: string
  email: string
  avatar?: string
  organization?: {
    name: string
    logo: string
    website?: string
  }
  bio?: string
  role?: string
  location?: string
  timezone?: string
  socialLinks?: SocialLink[]
  lastContacted?: string
  firstContacted?: string
  emailCount?: number
}

export interface EmailAttachment {
  name: string
  size: string
  type: string
  url: string
}

export interface Email {
  id: string
  subject: string
  sender: EmailSender
  recipients: EmailSender[]
  content: string
  date: string
  read: boolean
  flagged: boolean
  snoozed: boolean
  snoozeUntil?: Date
  archived: boolean
  deleted: boolean
  attachments?: EmailAttachment[]
  account: string
  categories?: EmailCategory[]
  letterCategory?: LetterCategory
  actionStatus?: ActionStatus
  hasReminder?: boolean
  actionDueDate?: string
  recordCreatedAt?: string
  originalImages?: string[]
  aiSuggestion?: string
  translatedContent?: { [language: string]: string }
  userNote?: string
}

export interface EmailAccount {
  id: string
  name: string
  email: string
  color: string
}
