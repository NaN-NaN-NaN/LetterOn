"use client"

import { useState } from "react"
import {
  ArrowLeft,
  Trash2,
  Star,
  CalendarIcon,
  Bell,
  CheckCircle2,
  Bot,
  Languages,
  ImageIcon,
  ChevronLeft,
  ChevronRight,
  StickyNote,
  Mail,
  Clock,
  Tag,
  Share2,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import type { Email, LetterCategory, ActionStatus } from "@/types/email"
import { formatDate } from "@/lib/utils"
import { Badge } from "@/components/ui/badge"
import { useToast } from "@/hooks/use-toast"
import { getCategoryDisplay, categoryOptions } from "@/lib/letter-categories"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"

interface EmailDetailProps {
  email: Email
  onClose: () => void
  onArchive: () => void
  onDelete: () => void
  onSnooze: (id: string, snoozeUntil: Date) => void
  onUpdateEmail: (id: string, updates: Partial<Email>) => void
}

export default function EmailDetail({
  email,
  onClose,
  onArchive,
  onDelete,
  onSnooze,
  onUpdateEmail,
}: EmailDetailProps) {
  const [chatMode, setChatMode] = useState(false)
  const [chatMessages, setChatMessages] = useState<{ role: "user" | "assistant"; content: string }[]>([])
  const [chatInput, setChatInput] = useState("")
  const [translateModalOpen, setTranslateModalOpen] = useState(false)
  const [selectedLanguage, setSelectedLanguage] = useState("")
  const [translatedContent, setTranslatedContent] = useState<string | null>(null)
  const [translatedAISuggestion, setTranslatedAISuggestion] = useState<string | null>(null)
  const [imageModalOpen, setImageModalOpen] = useState(false)
  const [currentImageIndex, setCurrentImageIndex] = useState(0)
  const [noteModalOpen, setNoteModalOpen] = useState(false)
  const [noteInput, setNoteInput] = useState(email.userNote || "")
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const { toast } = useToast()

  const categoryDisplay = getCategoryDisplay(email.letterCategory)

  const handleAskAI = () => {
    setChatMode(true)
    if (chatMessages.length === 0 && email.aiSuggestion) {
      setChatMessages([{ role: "assistant", content: email.aiSuggestion }])
    }
  }

  const handleSendMessage = () => {
    if (!chatInput.trim()) return

    setChatMessages([...chatMessages, { role: "user", content: chatInput }])
    setChatInput("")

    setTimeout(() => {
      setChatMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            "I understand your question. Based on the letter content, I can help you with that. What specific information would you like to know?",
        },
      ])
    }, 1000)
  }

  const handleTranslate = () => {
    if (!selectedLanguage) return

    // Simulate translation
    setTranslatedContent(`[Translated to ${selectedLanguage}]\n\n${email.content}`)
    if (email.aiSuggestion) {
      setTranslatedAISuggestion(`[Translated to ${selectedLanguage}]\n\n${email.aiSuggestion}`)
    }
    setTranslateModalOpen(false)
    toast({
      title: "Translation Complete",
      description: `Content translated to ${selectedLanguage}`,
    })
  }

  const handlePrevImage = () => {
    if (!email.originalImages) return
    setCurrentImageIndex((prev) => (prev === 0 ? email.originalImages!.length - 1 : prev - 1))
  }

  const handleNextImage = () => {
    if (!email.originalImages) return
    setCurrentImageIndex((prev) => (prev === email.originalImages!.length - 1 ? 0 : prev + 1))
  }

  const handleSaveNote = () => {
    onUpdateEmail(email.id, { userNote: noteInput })
    setNoteModalOpen(false)
    toast({
      title: "Note Saved",
      description: "Your note has been saved successfully.",
    })
  }

  const handleToggleStar = () => {
    onUpdateEmail(email.id, { flagged: !email.flagged })
    toast({
      title: email.flagged ? "Unstarred" : "Starred",
      description: email.flagged ? "Letter has been unstarred." : "Letter has been starred.",
    })
  }

  const handleUpdateCategory = (category: LetterCategory) => {
    onUpdateEmail(email.id, { letterCategory: category })
    toast({
      title: "Type Updated",
      description: "Letter type has been updated.",
    })
  }

  const handleUpdateReminder = (hasReminder: boolean) => {
    onUpdateEmail(email.id, { hasReminder })
    toast({
      title: hasReminder ? "Reminder Set" : "Reminder Removed",
      description: hasReminder ? "Reminder has been activated." : "Reminder has been removed.",
    })
  }

  const handleUpdateActionStatus = (status: ActionStatus) => {
    onUpdateEmail(email.id, { actionStatus: status })
    toast({
      title: "Action Status Updated",
      description: "Action status has been updated.",
    })
  }

  const handleConfirmDelete = () => {
    onDelete()
    setDeleteDialogOpen(false)
  }

  const handleShare = () => {
    // Simulate sharing functionality
    if (navigator.share) {
      navigator
        .share({
          title: email.subject,
          text: email.content.substring(0, 200),
        })
        .catch(() => {
          toast({
            title: "Share",
            description: "Sharing functionality triggered",
          })
        })
    } else {
      toast({
        title: "Share",
        description: "Share link copied to clipboard",
      })
    }
  }

  if (chatMode) {
    return (
      <div className="h-full flex flex-col">
        <div className="p-4 flex items-center justify-between border-b border-border/50">
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="icon" onClick={() => setChatMode(false)}>
              <ArrowLeft className="h-5 w-5" />
            </Button>
            <h2 className="text-lg font-medium">Chat with AI</h2>
          </div>
        </div>

        <ScrollArea className="flex-1 p-4">
          <div className="space-y-4 max-w-3xl mx-auto">
            {chatMessages.map((message, index) => (
              <div key={index} className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}>
                <div
                  className={`max-w-[80%] rounded-lg p-3 ${
                    message.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted"
                  }`}
                >
                  {message.content}
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>

        <div className="p-4 border-t border-border/50">
          <div className="flex gap-2">
            <Textarea
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              placeholder="Ask a question about this letter..."
              className="min-h-[60px]"
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault()
                  handleSendMessage()
                }
              }}
            />
            <Button onClick={handleSendMessage} disabled={!chatInput.trim()}>
              Send
            </Button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col">
      <div className="p-4 flex items-center justify-between border-b border-border/50">
        <div className="flex items-center gap-2 flex-1 min-w-0">
          <Button variant="ghost" size="icon" onClick={onClose} className="shrink-0 md:hidden">
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <h2 className="text-lg font-medium truncate">{email.subject}</h2>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <Button variant="ghost" size="icon" onClick={handleShare}>
            <Share2 className="h-5 w-5" />
          </Button>
          <Button variant="ghost" size="icon" onClick={() => setNoteModalOpen(true)}>
            <StickyNote className="h-5 w-5" />
          </Button>
          <Button variant="ghost" size="icon" onClick={handleToggleStar}>
            <Star className={`h-5 w-5 ${email.flagged ? "fill-yellow-400 text-yellow-400" : ""}`} />
          </Button>
          <Button variant="ghost" size="icon" onClick={() => setDeleteDialogOpen(true)}>
            <Trash2 className="h-5 w-5" />
          </Button>
        </div>
      </div>

      <div className="p-4 border-b border-border/50 bg-gray-50">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
          <div className="flex items-start gap-2">
            <Mail className="h-4 w-4 text-muted-foreground mt-0.5 shrink-0" />
            <span className="text-muted-foreground font-medium min-w-[100px] shrink-0">From:</span>
            <span className="truncate">{email.sender.name}</span>
          </div>

          <div className="flex items-start gap-2">
            <CalendarIcon className="h-4 w-4 text-muted-foreground mt-0.5 shrink-0" />
            <span className="text-muted-foreground font-medium min-w-[100px] shrink-0">Sent Date:</span>
            <span className="truncate">{formatDate(new Date(email.date))}</span>
          </div>

          <div className="flex items-start gap-2">
            <Clock className="h-4 w-4 text-muted-foreground mt-0.5 shrink-0" />
            <span className="text-muted-foreground font-medium min-w-[100px] shrink-0">Record Created:</span>
            <span className="truncate">
              {email.recordCreatedAt ? formatDate(new Date(email.recordCreatedAt)) : "N/A"}
            </span>
          </div>

          <div className="flex items-start gap-2">
            <CalendarIcon className="h-4 w-4 text-muted-foreground mt-0.5 shrink-0" />
            <span className="text-muted-foreground font-medium min-w-[100px] shrink-0">Action Due:</span>
            <span className="truncate">{email.actionDueDate ? formatDate(new Date(email.actionDueDate)) : "N/A"}</span>
          </div>

          <div className="flex items-start gap-2">
            <Tag className="h-4 w-4 text-muted-foreground mt-0.5 shrink-0" />
            <span className="text-muted-foreground font-medium min-w-[100px] shrink-0">Type:</span>
            <Select
              value={email.letterCategory}
              onValueChange={(value) => handleUpdateCategory(value as LetterCategory)}
            >
              <SelectTrigger className="h-7 w-auto border-0 bg-transparent p-0 hover:bg-muted">
                <SelectValue>
                  <Badge variant="outline" className={`text-xs ${categoryDisplay.color}`}>
                    {categoryDisplay.label}
                  </Badge>
                </SelectValue>
              </SelectTrigger>
              <SelectContent>
                {categoryOptions.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-start gap-2">
            <Bell className="h-4 w-4 text-muted-foreground mt-0.5 shrink-0" />
            <span className="text-muted-foreground font-medium min-w-[100px] shrink-0">Reminder:</span>
            <Select
              value={email.hasReminder ? "active" : "none"}
              onValueChange={(value) => handleUpdateReminder(value === "active")}
            >
              <SelectTrigger className="h-7 w-auto border-0 bg-transparent p-0 hover:bg-muted">
                <SelectValue>
                  <Badge
                    variant="outline"
                    className={`text-xs ${email.hasReminder ? "bg-yellow-100 text-yellow-700" : ""}`}
                  >
                    {email.hasReminder ? "Active" : "None"}
                  </Badge>
                </SelectValue>
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="none">None</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-start gap-2 md:col-span-2">
            <CheckCircle2 className="h-4 w-4 text-muted-foreground mt-0.5 shrink-0" />
            <span className="text-muted-foreground font-medium min-w-[100px] shrink-0">Action Status:</span>
            <Select
              value={email.actionStatus}
              onValueChange={(value) => handleUpdateActionStatus(value as ActionStatus)}
            >
              <SelectTrigger className="h-7 w-auto border-0 bg-transparent p-0 hover:bg-muted">
                <SelectValue>
                  <Badge
                    variant="outline"
                    className={`text-xs ${
                      email.actionStatus === "require-action"
                        ? "bg-red-100 text-red-700"
                        : email.actionStatus === "action-done"
                          ? "bg-green-100 text-green-700"
                          : "bg-gray-100 text-gray-700"
                    }`}
                  >
                    {email.actionStatus === "require-action"
                      ? "Require Action"
                      : email.actionStatus === "action-done"
                        ? "Action Done"
                        : "No Action Needed"}
                  </Badge>
                </SelectValue>
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="require-action">Require Action</SelectItem>
                <SelectItem value="action-done">Action Done</SelectItem>
                <SelectItem value="no-action-needed">No Action Needed</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {email.originalImages && email.originalImages.length > 0 && (
            <div className="flex items-start gap-2 md:col-span-2">
              <ImageIcon className="h-4 w-4 text-muted-foreground mt-0.5 shrink-0" />
              <span className="text-muted-foreground font-medium min-w-[100px] shrink-0">Original Images:</span>
              <div className="flex gap-2 flex-wrap">
                {email.originalImages.map((_, index) => (
                  <Button
                    key={index}
                    variant="outline"
                    size="sm"
                    className="h-8 w-8 p-0 bg-transparent"
                    onClick={() => {
                      setCurrentImageIndex(index)
                      setImageModalOpen(true)
                    }}
                  >
                    <ImageIcon className="h-4 w-4" />
                  </Button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {email.userNote && (
        <div className="p-4 border-b border-border/50" style={{ backgroundColor: "#DFBE7D" }}>
          <div className="flex items-start gap-3">
            <StickyNote className="h-5 w-5 text-amber-900 shrink-0 mt-0.5" />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-amber-900 mb-1">Your Note</p>
              <p className="text-sm text-amber-900">{email.userNote}</p>
            </div>
          </div>
        </div>
      )}

      {email.aiSuggestion && !chatMode && (
        <div className="p-4 bg-blue-50 border-b border-border/50">
          {translatedAISuggestion ? (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <div className="flex items-start gap-3">
                <Bot className="h-5 w-5 text-blue-600 shrink-0 mt-0.5" />
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium text-blue-900 mb-1">AI Suggestion (Original)</p>
                  <p className="text-sm text-blue-900">{email.aiSuggestion}</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <Bot className="h-5 w-5 text-blue-600 shrink-0 mt-0.5" />
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium text-blue-900 mb-1">AI Suggestion (Translated)</p>
                  <p className="text-sm text-blue-900">{translatedAISuggestion}</p>
                </div>
              </div>
            </div>
          ) : (
            <div className="flex items-start gap-3">
              <Bot className="h-5 w-5 text-blue-600 shrink-0 mt-0.5" />
              <div className="flex-1 min-w-0">
                <p className="text-sm text-blue-900">{email.aiSuggestion}</p>
              </div>
            </div>
          )}
        </div>
      )}

      <ScrollArea className="flex-1">
        <div className="p-4">
          {translatedContent ? (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <div>
                <h3 className="text-sm font-medium mb-2">Original</h3>
                <div className="prose prose-sm max-w-none">
                  {email.content.split("\n\n").map((paragraph, index) => (
                    <p key={index}>{paragraph}</p>
                  ))}
                </div>
              </div>
              <div>
                <h3 className="text-sm font-medium mb-2">Translated</h3>
                <div className="prose prose-sm max-w-none">
                  {translatedContent.split("\n\n").map((paragraph, index) => (
                    <p key={index}>{paragraph}</p>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="prose prose-sm max-w-none">
              {email.content.split("\n\n").map((paragraph, index) => (
                <p key={index}>{paragraph}</p>
              ))}
            </div>
          )}

          {email.attachments && email.attachments.length > 0 && (
            <div className="mt-6">
              <h3 className="text-sm font-medium mb-2">Attachments ({email.attachments.length})</h3>
              <div className="flex flex-wrap gap-2">
                {email.attachments.map((attachment, index) => (
                  <div
                    key={index}
                    className="border rounded-md p-2 flex items-center gap-2 bg-muted/50 border-border/50"
                  >
                    <div className="text-sm">
                      <div>{attachment.name}</div>
                      <div className="text-xs text-muted-foreground">{attachment.size}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </ScrollArea>

      <div className="p-4 border-t border-border/50">
        <div className="flex items-center gap-2 flex-wrap">
          <Button variant="default" className="flex-1 min-w-[120px]" onClick={handleAskAI}>
            <Bot className="mr-2 h-4 w-4" />
            Ask AI
          </Button>
          <Button
            variant="outline"
            className="flex-1 min-w-[120px] bg-transparent"
            onClick={() => setTranslateModalOpen(true)}
          >
            <Languages className="mr-2 h-4 w-4" />
            Translate
          </Button>
        </div>
      </div>

      {/* Note Modal */}
      <Dialog open={noteModalOpen} onOpenChange={setNoteModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Note</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <Textarea
              value={noteInput}
              onChange={(e) => setNoteInput(e.target.value)}
              placeholder="Enter your note here..."
              className="min-h-[120px]"
            />
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setNoteModalOpen(false)}>
                Cancel
              </Button>
              <Button onClick={handleSaveNote}>Save</Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Are you sure?</AlertDialogTitle>
            <AlertDialogDescription>
              This action cannot be undone. This will permanently delete this letter.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleConfirmDelete}>Delete</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Translation Modal */}
      <Dialog open={translateModalOpen} onOpenChange={setTranslateModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Translate Letter</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-2 block">Select Language</label>
              <Select value={selectedLanguage} onValueChange={setSelectedLanguage}>
                <SelectTrigger>
                  <SelectValue placeholder="Choose a language" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Chinese (Simplified)">Chinese (Simplified)</SelectItem>
                  <SelectItem value="Chinese (Traditional)">Chinese (Traditional)</SelectItem>
                  <SelectItem value="Spanish">Spanish</SelectItem>
                  <SelectItem value="French">French</SelectItem>
                  <SelectItem value="German">German</SelectItem>
                  <SelectItem value="Japanese">Japanese</SelectItem>
                  <SelectItem value="Korean">Korean</SelectItem>
                  <SelectItem value="English">English</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setTranslateModalOpen(false)}>
                Cancel
              </Button>
              <Button onClick={handleTranslate} disabled={!selectedLanguage}>
                Translate
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Image Modal */}
      <Dialog open={imageModalOpen} onOpenChange={setImageModalOpen}>
        <DialogContent className="max-w-4xl">
          <DialogHeader>
            <DialogTitle>
              Original Image {currentImageIndex + 1} of {email.originalImages?.length || 0}
            </DialogTitle>
          </DialogHeader>
          <div className="relative">
            {email.originalImages && email.originalImages[currentImageIndex] && (
              <img
                src={email.originalImages[currentImageIndex] || "/placeholder.svg"}
                alt={`Original letter ${currentImageIndex + 1}`}
                className="w-full h-auto max-h-[70vh] object-contain"
              />
            )}
            {email.originalImages && email.originalImages.length > 1 && (
              <div className="absolute inset-y-0 left-0 right-0 flex items-center justify-between px-4 pointer-events-none">
                <Button variant="secondary" size="icon" className="pointer-events-auto" onClick={handlePrevImage}>
                  <ChevronLeft className="h-6 w-6" />
                </Button>
                <Button variant="secondary" size="icon" className="pointer-events-auto" onClick={handleNextImage}>
                  <ChevronRight className="h-6 w-6" />
                </Button>
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}
