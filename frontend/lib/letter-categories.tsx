import type React from "react"
import type { LetterCategory } from "@/types/email"
import {
  FileText,
  DollarSign,
  Building2,
  Briefcase,
  GraduationCap,
  Heart,
  Scale,
  Package,
  Mail,
  Home,
  CreditCard,
  Megaphone,
  Plane,
  HandHeart,
  HelpCircle,
} from "lucide-react"

export function getCategoryDisplay(category?: LetterCategory) {
  const displays: Record<
    LetterCategory,
    {
      icon: React.ReactNode
      label: string
      color: string
    }
  > = {
    "official-government": {
      icon: <FileText className="h-5 w-5 stroke-white" />,
      label: "Official",
      color: "bg-[#144B73] text-white",
    },
    "financial-billing": {
      icon: <DollarSign className="h-5 w-5 stroke-white" />,
      label: "Financial",
      color: "bg-[#DFBE7D] text-gray-800",
    },
    "banking-insurance": {
      icon: <Building2 className="h-5 w-5 stroke-white" />,
      label: "Banking",
      color: "bg-[#144B73] text-white",
    },
    "employment-hr": {
      icon: <Briefcase className="h-5 w-5 stroke-white" />,
      label: "Employment",
      color: "bg-[#DFBE7D] text-gray-800",
    },
    "education-academic": {
      icon: <GraduationCap className="h-5 w-5 stroke-white" />,
      label: "Education",
      color: "bg-[#144B73] text-white",
    },
    "healthcare-medical": {
      icon: <Heart className="h-5 w-5 stroke-white" />,
      label: "Healthcare",
      color: "bg-[#DFBE7D] text-gray-800",
    },
    "legal-compliance": {
      icon: <Scale className="h-5 w-5 stroke-white" />,
      label: "Legal",
      color: "bg-[#144B73] text-white",
    },
    "logistics-delivery": {
      icon: <Package className="h-5 w-5 stroke-white" />,
      label: "Logistics",
      color: "bg-[#DFBE7D] text-gray-800",
    },
    "personal-social": {
      icon: <Mail className="h-5 w-5 stroke-white" />,
      label: "Personal",
      color: "bg-[#144B73] text-white",
    },
    "real-estate-utilities": {
      icon: <Home className="h-5 w-5 stroke-white" />,
      label: "Real Estate",
      color: "bg-[#DFBE7D] text-gray-800",
    },
    "subscription-membership": {
      icon: <CreditCard className="h-5 w-5 stroke-white" />,
      label: "Subscription",
      color: "bg-[#144B73] text-white",
    },
    "marketing-promotions": {
      icon: <Megaphone className="h-5 w-5 stroke-white" />,
      label: "Marketing",
      color: "bg-[#DFBE7D] text-gray-800",
    },
    "travel-ticketing": {
      icon: <Plane className="h-5 w-5 stroke-white" />,
      label: "Travel",
      color: "bg-[#144B73] text-white",
    },
    "nonprofit-ngo": {
      icon: <HandHeart className="h-5 w-5 stroke-white" />,
      label: "Nonprofit",
      color: "bg-[#DFBE7D] text-gray-800",
    },
    miscellaneous: {
      icon: <HelpCircle className="h-5 w-5 stroke-white" />,
      label: "Miscellaneous",
      color: "bg-gray-500 text-white",
    },
  }

  return displays[category || "miscellaneous"]
}

export const categoryOptions: { value: LetterCategory; label: string }[] = [
  { value: "official-government", label: "Official" },
  { value: "financial-billing", label: "Financial" },
  { value: "banking-insurance", label: "Banking" },
  { value: "employment-hr", label: "Employment" },
  { value: "education-academic", label: "Education" },
  { value: "healthcare-medical", label: "Healthcare" },
  { value: "legal-compliance", label: "Legal" },
  { value: "logistics-delivery", label: "Logistics" },
  { value: "personal-social", label: "Personal" },
  { value: "real-estate-utilities", label: "Real Estate" },
  { value: "subscription-membership", label: "Subscription" },
  { value: "marketing-promotions", label: "Marketing" },
  { value: "travel-ticketing", label: "Travel" },
  { value: "nonprofit-ngo", label: "Nonprofit" },
  { value: "miscellaneous", label: "Miscellaneous" },
]
