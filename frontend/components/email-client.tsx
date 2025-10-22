"use client"

import { useState, useEffect, useMemo } from "react"
import EmailList from "@/components/email-list"
import EmailDetail from "@/components/email-detail"
import UploadLetters from "@/components/upload-letters"
import AuthPage from "@/components/auth-page"
import type { Email, EmailAccount, EmailFolder } from "@/types/email"
import { mockEmails, mockAccounts } from "@/lib/mock-data"
import { useMobile } from "@/hooks/use-mobile"
import { useToast } from "@/hooks/use-toast"
import { ResizablePanelGroup, ResizablePanel, ResizableHandle } from "@/components/ui/resizable"
import { PenSquare } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog"
import { ChevronRight } from "lucide-react"

export default function EmailClient() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [selectedFolder, setSelectedFolder] = useState<EmailFolder>("unified")
  const [selectedEmail, setSelectedEmail] = useState<Email | null>(null)
  const [emails, setEmails] = useState<Email[]>(mockEmails)
  const [accounts, setAccounts] = useState<EmailAccount[]>(mockAccounts)
  const [composeMode, setComposeMode] = useState(false)
  const [detailOpen, setDetailOpen] = useState(false)
  const isMobile = useMobile()
  const { toast } = useToast()

  const [showGuidance, setShowGuidance] = useState(true)
  const [guidanceStep, setGuidanceStep] = useState(1)

  const filteredEmails = useMemo(() => {
    return emails.filter((email) => {
      if (email.deleted) return false
      if (email.snoozed) return selectedFolder === "snoozed"
      if (email.archived) return selectedFolder === "archived"

      if (selectedFolder === "unified") return !email.archived && !email.snoozed
      if (selectedFolder === "unread") return !email.read && !email.archived && !email.snoozed
      if (selectedFolder === "flagged") return email.flagged && !email.archived && !email.snoozed

      return email.account === selectedFolder && !email.archived && !email.snoozed
    })
  }, [emails, selectedFolder])

  useEffect(() => {
    if (!selectedEmail) {
      setDetailOpen(false)
    }
  }, [selectedEmail])

  const handleEmailSelect = (email: Email) => {
    setSelectedEmail(email)
    setComposeMode(false)

    setEmails(emails.map((e) => (e.id === email.id ? { ...e, read: true } : e)))

    if (isMobile) {
      setDetailOpen(true)
    }
  }

  const handleSnoozeEmail = (emailId: string, snoozeUntil: Date) => {
    setEmails(emails.map((email) => (email.id === emailId ? { ...email, snoozed: true, snoozeUntil } : email)))
    toast({
      title: "Email Snoozed",
      description: `Email will reappear on ${snoozeUntil.toLocaleDateString()}`,
    })
  }

  const handleArchiveEmail = (emailId: string) => {
    setEmails(emails.map((email) => (email.id === emailId ? { ...email, archived: true } : email)))

    if (selectedEmail?.id === emailId) {
      setSelectedEmail(null)
    }

    toast({
      title: "Email Archived",
      description: "Email has been moved to archive.",
    })
  }

  const handleDeleteEmail = (emailId: string) => {
    setEmails(emails.map((email) => (email.id === emailId ? { ...email, deleted: true } : email)))

    if (selectedEmail?.id === emailId) {
      setSelectedEmail(null)
    }

    toast({
      title: "Email Deleted",
      description: "Email has been deleted.",
    })
  }

  const handleUpdateEmail = (emailId: string, updates: Partial<Email>) => {
    setEmails(emails.map((email) => (email.id === emailId ? { ...email, ...updates } : email)))

    if (selectedEmail?.id === emailId) {
      setSelectedEmail({ ...selectedEmail, ...updates })
    }
  }

  const handleCreateLetter = (letter: Email) => {
    setEmails([letter, ...emails])
    setSelectedEmail(letter)
    setComposeMode(false)

    if (isMobile) {
      setDetailOpen(true)
    }
  }

  const handleLogout = () => {
    setIsAuthenticated(false)
    setSelectedEmail(null)
    setComposeMode(false)
    toast({
      title: "Logged Out",
      description: "You have been successfully logged out.",
    })
  }

  useEffect(() => {
    if (emails.length > 0 && !selectedEmail && !composeMode) {
      const firstVisibleEmail = filteredEmails[0]
      if (firstVisibleEmail) {
        setSelectedEmail(firstVisibleEmail)
        setEmails(emails.map((e) => (e.id === firstVisibleEmail.id ? { ...e, read: true } : e)))
      }
    }
  }, [emails, filteredEmails, selectedEmail, composeMode])

  useEffect(() => {
    const guidanceCompleted = localStorage.getItem("letterOnGuidanceCompleted")
    if (guidanceCompleted) {
      setShowGuidance(false)
    }
  }, [])

  const handleNextGuidanceStep = () => {
    if (guidanceStep < 4) {
      setGuidanceStep(guidanceStep + 1)
    } else {
      setShowGuidance(false)
      localStorage.setItem("letterOnGuidanceCompleted", "true")
    }
  }

  const handleSkipGuidance = () => {
    setShowGuidance(false)
    localStorage.setItem("letterOnGuidanceCompleted", "true")
  }

  if (!isAuthenticated) {
    return <AuthPage onAuthenticated={() => setIsAuthenticated(true)} />
  }

  return (
    <div className="flex h-screen w-full justify-center bg-background overflow-x-hidden">
      <Dialog open={showGuidance && isAuthenticated} onOpenChange={setShowGuidance}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Welcome to LetterON!</DialogTitle>
            <DialogDescription>Let's get you started with a quick tour</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            {guidanceStep === 1 && (
              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold">
                    1
                  </div>
                  <h3 className="font-semibold">Upload Letter Images</h3>
                </div>
                <p className="text-sm text-muted-foreground pl-11">
                  Click the "Add New Letter Record" button to upload images of your physical letters. You can upload up
                  to 3 images per letter.
                </p>
              </div>
            )}
            {guidanceStep === 2 && (
              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold">
                    2
                  </div>
                  <h3 className="font-semibold">Review & Confirm</h3>
                </div>
                <p className="text-sm text-muted-foreground pl-11">
                  After uploading, our AI will analyze the letter and extract key information. Review the details and
                  add translations if needed before confirming.
                </p>
              </div>
            )}
            {guidanceStep === 3 && (
              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold">
                    3
                  </div>
                  <h3 className="font-semibold">Filter Your Letters</h3>
                </div>
                <p className="text-sm text-muted-foreground pl-11">
                  Use the filter button to organize your letters by type, date, action status, and more. Filter chips
                  make it easy to see what's active.
                </p>
              </div>
            )}
            {guidanceStep === 4 && (
              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold">
                    4
                  </div>
                  <h3 className="font-semibold">Chat with AI</h3>
                </div>
                <p className="text-sm text-muted-foreground pl-11">
                  Get AI-powered suggestions for each letter. Click "Ask AI" to have a conversation about the letter
                  content and get personalized advice.
                </p>
              </div>
            )}
            <div className="flex justify-between items-center pt-4">
              <Button variant="ghost" onClick={handleSkipGuidance}>
                Skip
              </Button>
              <div className="flex gap-1">
                {[1, 2, 3, 4].map((step) => (
                  <div
                    key={step}
                    className={`w-2 h-2 rounded-full ${step === guidanceStep ? "bg-primary" : "bg-muted"}`}
                  />
                ))}
              </div>
              <Button onClick={handleNextGuidanceStep}>
                {guidanceStep === 4 ? "Get Started" : "Next"}
                <ChevronRight className="ml-1 h-4 w-4" />
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      <div className="flex h-full w-full max-w-[1600px] overflow-x-hidden relative">
        {isMobile ? (
          <div className="flex-1 w-full overflow-x-hidden min-w-0">
            {composeMode ? (
              <UploadLetters onClose={() => setComposeMode(false)} onCreateLetter={handleCreateLetter} />
            ) : detailOpen && selectedEmail ? (
              <EmailDetail
                email={selectedEmail}
                onClose={() => setDetailOpen(false)}
                onArchive={() => handleArchiveEmail(selectedEmail.id)}
                onDelete={() => handleDeleteEmail(selectedEmail.id)}
                onSnooze={handleSnoozeEmail}
                onUpdateEmail={handleUpdateEmail}
              />
            ) : (
              <>
                <EmailList
                  emails={filteredEmails}
                  selectedEmail={selectedEmail}
                  onSelectEmail={handleEmailSelect}
                  onToggleSidebar={() => {}}
                  onArchiveEmail={handleArchiveEmail}
                  onDeleteEmail={handleDeleteEmail}
                  onSnoozeEmail={handleSnoozeEmail}
                  selectedFolder={selectedFolder}
                  onCompose={() => setComposeMode(true)}
                  onLogout={handleLogout}
                />
                <div className="fixed bottom-0 left-0 right-0 p-4 bg-background/95 backdrop-blur-sm border-t border-border/50 z-50">
                  <Button
                    variant="default"
                    size="lg"
                    className="w-full shadow-lg h-14"
                    onClick={() => setComposeMode(true)}
                  >
                    <PenSquare className="mr-2 h-5 w-5" />
                    Add New Letter Record
                  </Button>
                </div>
              </>
            )}
          </div>
        ) : (
          <ResizablePanelGroup direction="horizontal" className="flex-1 overflow-hidden">
            <ResizablePanel defaultSize={40} minSize={40} maxSize={40} className="min-w-0">
              <EmailList
                emails={filteredEmails}
                selectedEmail={selectedEmail}
                onSelectEmail={handleEmailSelect}
                onToggleSidebar={() => {}}
                onArchiveEmail={handleArchiveEmail}
                onDeleteEmail={handleDeleteEmail}
                onSnoozeEmail={handleSnoozeEmail}
                selectedFolder={selectedFolder}
                onCompose={() => setComposeMode(true)}
                onLogout={handleLogout}
              />
            </ResizablePanel>

            <ResizableHandle withHandle />

            <ResizablePanel defaultSize={60} className="min-w-0">
              {composeMode ? (
                <UploadLetters onClose={() => setComposeMode(false)} onCreateLetter={handleCreateLetter} />
              ) : selectedEmail ? (
                <EmailDetail
                  email={selectedEmail}
                  onClose={() => setSelectedEmail(null)}
                  onArchive={() => handleArchiveEmail(selectedEmail.id)}
                  onDelete={() => handleDeleteEmail(selectedEmail.id)}
                  onSnooze={handleSnoozeEmail}
                  onUpdateEmail={handleUpdateEmail}
                />
              ) : (
                <div className="flex h-full items-center justify-center text-muted-foreground">
                  <p>Select an email to view</p>
                </div>
              )}
            </ResizablePanel>
          </ResizablePanelGroup>
        )}
      </div>
    </div>
  )
}
