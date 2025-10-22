"use client"

import { Checkbox } from "@/components/ui/checkbox"

import { useState, useRef, useEffect } from "react"
import {
  Archive,
  Trash2,
  Clock,
  PenSquare,
  SlidersHorizontal,
  Star,
  CalendarIcon,
  Tag,
  Bell,
  CheckCircle2,
  User,
  LogOut,
  X,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Calendar } from "@/components/ui/calendar"
import { Input } from "@/components/ui/input"
import type { Email, EmailFolder, LetterCategory, ActionStatus } from "@/types/email"
import { formatDistanceToNow } from "@/lib/utils"
import { Badge } from "@/components/ui/badge"
import Image from "next/image"
import { Label } from "@/components/ui/label"
import { getCategoryDisplay, categoryOptions } from "@/lib/letter-categories"
import { Separator } from "@/components/ui/separator"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { Dialog, DialogContent } from "@/components/ui/dialog"
import { useMobile } from "@/hooks/use-mobile"

interface EmailListProps {
  emails: Email[]
  selectedEmail: Email | null
  selectedFolder: EmailFolder
  onSelectEmail: (email: Email) => void
  onToggleSidebar: () => void
  onArchiveEmail: (id: string) => void
  onDeleteEmail: (id: string) => void
  onSnoozeEmail: (id: string, snoozeUntil: Date) => void
  onCompose: () => void
  onLogout: () => void
}

export default function EmailList({
  emails,
  selectedEmail,
  selectedFolder,
  onSelectEmail,
  onToggleSidebar,
  onArchiveEmail,
  onDeleteEmail,
  onSnoozeEmail,
  onCompose,
  onLogout,
}: EmailListProps) {
  const [searchQuery, setSearchQuery] = useState("")
  const [filterOpen, setFilterOpen] = useState(false)
  const isMobile = useMobile()

  const [selectedActionStatuses, setSelectedActionStatuses] = useState<ActionStatus[]>([])
  const [appliedActionStatuses, setAppliedActionStatuses] = useState<ActionStatus[]>([])

  const [selectedCategories, setSelectedCategories] = useState<LetterCategory[]>([])
  const [appliedCategories, setAppliedCategories] = useState<LetterCategory[]>([])

  const [actionDueDateRange, setActionDueDateRange] = useState<{ from?: Date; to?: Date }>({})
  const [appliedActionDueDateRange, setAppliedActionDueDateRange] = useState<{ from?: Date; to?: Date }>({})

  const [sentDateRange, setSentDateRange] = useState<{ from?: Date; to?: Date }>({})
  const [appliedSentDateRange, setAppliedSentDateRange] = useState<{ from?: Date; to?: Date }>({})

  const [createdDateRange, setCreatedDateRange] = useState<{ from?: Date; to?: Date }>({})
  const [appliedCreatedDateRange, setAppliedCreatedDateRange] = useState<{ from?: Date; to?: Date }>({})

  const [needsReminder, setNeedsReminder] = useState(false)
  const [appliedNeedsReminder, setAppliedNeedsReminder] = useState(false)

  const [onlyFavorites, setOnlyFavorites] = useState(false)
  const [appliedOnlyFavorites, setAppliedOnlyFavorites] = useState(false)

  const [actionDueFromOpen, setActionDueFromOpen] = useState(false)
  const [actionDueToOpen, setActionDueToOpen] = useState(false)
  const [sentFromOpen, setSentFromOpen] = useState(false)
  const [sentToOpen, setSentToOpen] = useState(false)
  const [createdFromOpen, setCreatedFromOpen] = useState(false)
  const [createdToOpen, setCreatedToOpen] = useState(false)

  const [typeDropdownOpen, setTypeDropdownOpen] = useState(false)
  const [actionStatusDropdownOpen, setActionStatusDropdownOpen] = useState(false)

  const filtersChanged =
    JSON.stringify(selectedCategories) !== JSON.stringify(appliedCategories) ||
    JSON.stringify(actionDueDateRange) !== JSON.stringify(appliedActionDueDateRange) ||
    JSON.stringify(sentDateRange) !== JSON.stringify(appliedSentDateRange) ||
    JSON.stringify(createdDateRange) !== JSON.stringify(appliedCreatedDateRange) ||
    JSON.stringify(selectedActionStatuses) !== JSON.stringify(appliedActionStatuses) ||
    needsReminder !== appliedNeedsReminder ||
    onlyFavorites !== appliedOnlyFavorites

  const applyFilters = () => {
    setAppliedCategories(selectedCategories)
    setAppliedActionDueDateRange(actionDueDateRange)
    setAppliedSentDateRange(sentDateRange)
    setAppliedCreatedDateRange(createdDateRange)
    setAppliedActionStatuses(selectedActionStatuses)
    setAppliedNeedsReminder(needsReminder)
    setAppliedOnlyFavorites(onlyFavorites)
    setFilterOpen(false)
  }

  const cancelFilters = () => {
    setSelectedCategories(appliedCategories)
    setActionDueDateRange(appliedActionDueDateRange)
    setSentDateRange(appliedSentDateRange)
    setCreatedDateRange(appliedCreatedDateRange)
    setSelectedActionStatuses(appliedActionStatuses)
    setNeedsReminder(appliedNeedsReminder)
    setOnlyFavorites(appliedOnlyFavorites)
    setFilterOpen(false)
  }

  const removeFilterChip = (
    type: "category" | "actionStatus" | "actionDueDate" | "sentDate" | "createdDate" | "reminder" | "favorite",
    value?: any,
  ) => {
    if (type === "category" && value) {
      const newCategories = appliedCategories.filter((c) => c !== value)
      setAppliedCategories(newCategories)
      setSelectedCategories(newCategories)
    } else if (type === "actionStatus" && value) {
      const newStatuses = appliedActionStatuses.filter((s) => s !== value)
      setAppliedActionStatuses(newStatuses)
      setSelectedActionStatuses(newStatuses)
    } else if (type === "actionDueDate") {
      setAppliedActionDueDateRange({})
      setActionDueDateRange({})
    } else if (type === "sentDate") {
      setAppliedSentDateRange({})
      setSentDateRange({})
    } else if (type === "createdDate") {
      setAppliedCreatedDateRange({})
      setCreatedDateRange({})
    } else if (type === "reminder") {
      setAppliedNeedsReminder(false)
      setNeedsReminder(false)
    } else if (type === "favorite") {
      setAppliedOnlyFavorites(false)
      setOnlyFavorites(false)
    }
  }

  const filteredEmails = emails.filter((email) => {
    const matchesSearch =
      email.subject.toLowerCase().includes(searchQuery.toLowerCase()) ||
      email.sender.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      email.content.toLowerCase().includes(searchQuery.toLowerCase())

    const matchesCategory = !appliedCategories.length || appliedCategories.includes(email.letterCategory!)
    const matchesActionStatus = !appliedActionStatuses.length || appliedActionStatuses.includes(email.actionStatus!)

    const matchesActionDueDate =
      (!appliedActionDueDateRange.from ||
        (email.actionDueDate && new Date(email.actionDueDate) >= appliedActionDueDateRange.from)) &&
      (!appliedActionDueDateRange.to ||
        (email.actionDueDate && new Date(email.actionDueDate) <= appliedActionDueDateRange.to))

    const matchesSentDate =
      (!appliedSentDateRange.from || new Date(email.date) >= appliedSentDateRange.from) &&
      (!appliedSentDateRange.to || new Date(email.date) <= appliedSentDateRange.to)

    const matchesCreatedDate =
      (!appliedCreatedDateRange.from ||
        (email.recordCreatedAt && new Date(email.recordCreatedAt) >= appliedCreatedDateRange.from)) &&
      (!appliedCreatedDateRange.to ||
        (email.recordCreatedAt && new Date(email.recordCreatedAt) <= appliedCreatedDateRange.to))

    const matchesReminder = !appliedNeedsReminder || email.hasReminder
    const matchesFavorite = !appliedOnlyFavorites || email.flagged

    return (
      matchesSearch &&
      matchesCategory &&
      matchesActionStatus &&
      matchesActionDueDate &&
      matchesSentDate &&
      matchesCreatedDate &&
      matchesReminder &&
      matchesFavorite
    )
  })

  const toggleCategory = (category: LetterCategory) => {
    setSelectedCategories((prev) =>
      prev.includes(category) ? prev.filter((c) => c !== category) : [...prev, category],
    )
  }

  const toggleActionStatus = (status: ActionStatus) => {
    setSelectedActionStatuses((prev) => (prev.includes(status) ? prev.filter((s) => s !== status) : [...prev, status]))
  }

  const FilterContent = () => (
    <div className="space-y-6 min-w-0 max-w-full overflow-hidden">
      <div className="min-w-0 max-w-full">
        <div className="flex items-center gap-2 mb-3">
          <CalendarIcon className="h-4 w-4 text-muted-foreground shrink-0" />
          <Label className="text-sm font-medium">Action Due Date</Label>
        </div>
        <div className="flex gap-2 text-xs min-w-0 max-w-full">
          <Popover open={actionDueFromOpen} onOpenChange={setActionDueFromOpen}>
            <PopoverTrigger asChild>
              <Button
                variant="outline"
                size="sm"
                className="flex-1 bg-transparent justify-start text-xs min-w-0 max-w-[calc(50%-4px)]"
              >
                <span className="truncate">
                  From: {actionDueDateRange.from ? actionDueDateRange.from.toLocaleDateString() : "Any"}
                </span>
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-auto p-0" align="start">
              <div className="p-2">
                <Button
                  variant="ghost"
                  size="sm"
                  className="w-full mb-2"
                  onClick={() => {
                    setActionDueDateRange((prev) => ({ ...prev, from: undefined }))
                    setActionDueFromOpen(false)
                  }}
                >
                  Clear
                </Button>
                <Calendar
                  mode="single"
                  selected={actionDueDateRange.from}
                  onSelect={(date) => {
                    setActionDueDateRange((prev) => ({ ...prev, from: date }))
                    setActionDueFromOpen(false)
                  }}
                  initialFocus
                />
              </div>
            </PopoverContent>
          </Popover>

          <Popover open={actionDueToOpen} onOpenChange={setActionDueToOpen}>
            <PopoverTrigger asChild>
              <Button
                variant="outline"
                size="sm"
                className="flex-1 bg-transparent justify-start text-xs min-w-0 max-w-[calc(50%-4px)]"
              >
                <span className="truncate">
                  To: {actionDueDateRange.to ? actionDueDateRange.to.toLocaleDateString() : "Any"}
                </span>
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-auto p-0" align="start">
              <div className="p-2">
                <Button
                  variant="ghost"
                  size="sm"
                  className="w-full mb-2"
                  onClick={() => {
                    setActionDueDateRange((prev) => ({ ...prev, to: undefined }))
                    setActionDueToOpen(false)
                  }}
                >
                  Clear
                </Button>
                <Calendar
                  mode="single"
                  selected={actionDueDateRange.to}
                  onSelect={(date) => {
                    setActionDueDateRange((prev) => ({ ...prev, to: date }))
                    setActionDueToOpen(false)
                  }}
                  initialFocus
                />
              </div>
            </PopoverContent>
          </Popover>
        </div>
      </div>

      <Separator className="my-6" />

      <div className="min-w-0 max-w-full">
        <div className="flex items-center gap-2 mb-3">
          <CalendarIcon className="h-4 w-4 text-muted-foreground shrink-0" />
          <Label className="text-sm font-medium">Sent Date</Label>
        </div>
        <div className="flex gap-2 text-xs min-w-0 max-w-full">
          <Popover open={sentFromOpen} onOpenChange={setSentFromOpen}>
            <PopoverTrigger asChild>
              <Button
                variant="outline"
                size="sm"
                className="flex-1 bg-transparent justify-start text-xs min-w-0 max-w-[calc(50%-4px)]"
              >
                <span className="truncate">
                  From: {sentDateRange.from ? sentDateRange.from.toLocaleDateString() : "Any"}
                </span>
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-auto p-0" align="start">
              <div className="p-2">
                <Button
                  variant="ghost"
                  size="sm"
                  className="w-full mb-2"
                  onClick={() => {
                    setSentDateRange((prev) => ({ ...prev, from: undefined }))
                    setSentFromOpen(false)
                  }}
                >
                  Clear
                </Button>
                <Calendar
                  mode="single"
                  selected={sentDateRange.from}
                  onSelect={(date) => {
                    setSentDateRange((prev) => ({ ...prev, from: date }))
                    setSentFromOpen(false)
                  }}
                  initialFocus
                />
              </div>
            </PopoverContent>
          </Popover>

          <Popover open={sentToOpen} onOpenChange={setSentToOpen}>
            <PopoverTrigger asChild>
              <Button
                variant="outline"
                size="sm"
                className="flex-1 bg-transparent justify-start text-xs min-w-0 max-w-[calc(50%-4px)]"
              >
                <span className="truncate">To: {sentDateRange.to ? sentDateRange.to.toLocaleDateString() : "Any"}</span>
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-auto p-0" align="start">
              <div className="p-2">
                <Button
                  variant="ghost"
                  size="sm"
                  className="w-full mb-2"
                  onClick={() => {
                    setSentDateRange((prev) => ({ ...prev, to: undefined }))
                    setSentToOpen(false)
                  }}
                >
                  Clear
                </Button>
                <Calendar
                  mode="single"
                  selected={sentDateRange.to}
                  onSelect={(date) => {
                    setSentDateRange((prev) => ({ ...prev, to: date }))
                    setSentToOpen(false)
                  }}
                  initialFocus
                />
              </div>
            </PopoverContent>
          </Popover>
        </div>
      </div>

      <Separator className="my-6" />

      <div className="min-w-0 max-w-full">
        <div className="flex items-center gap-2 mb-3">
          <CalendarIcon className="h-4 w-4 text-muted-foreground shrink-0" />
          <Label className="text-sm font-medium">Item Created Date</Label>
        </div>
        <div className="flex gap-2 text-xs min-w-0 max-w-full">
          <Popover open={createdFromOpen} onOpenChange={setCreatedFromOpen}>
            <PopoverTrigger asChild>
              <Button
                variant="outline"
                size="sm"
                className="flex-1 bg-transparent justify-start text-xs min-w-0 max-w-[calc(50%-4px)]"
              >
                <span className="truncate">
                  From: {createdDateRange.from ? createdDateRange.from.toLocaleDateString() : "Any"}
                </span>
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-auto p-0" align="start">
              <div className="p-2">
                <Button
                  variant="ghost"
                  size="sm"
                  className="w-full mb-2"
                  onClick={() => {
                    setCreatedDateRange((prev) => ({ ...prev, from: undefined }))
                    setCreatedFromOpen(false)
                  }}
                >
                  Clear
                </Button>
                <Calendar
                  mode="single"
                  selected={createdDateRange.from}
                  onSelect={(date) => {
                    setCreatedDateRange((prev) => ({ ...prev, from: date }))
                    setCreatedFromOpen(false)
                  }}
                  initialFocus
                />
              </div>
            </PopoverContent>
          </Popover>

          <Popover open={createdToOpen} onOpenChange={setCreatedToOpen}>
            <PopoverTrigger asChild>
              <Button
                variant="outline"
                size="sm"
                className="flex-1 bg-transparent justify-start text-xs min-w-0 max-w-[calc(50%-4px)]"
              >
                <span className="truncate">
                  To: {createdDateRange.to ? createdDateRange.to.toLocaleDateString() : "Any"}
                </span>
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-auto p-0" align="start">
              <div className="p-2">
                <Button
                  variant="ghost"
                  size="sm"
                  className="w-full mb-2"
                  onClick={() => {
                    setCreatedDateRange((prev) => ({ ...prev, to: undefined }))
                    setCreatedToOpen(false)
                  }}
                >
                  Clear
                </Button>
                <Calendar
                  mode="single"
                  selected={createdDateRange.to}
                  onSelect={(date) => {
                    setCreatedDateRange((prev) => ({ ...prev, to: date }))
                    setCreatedToOpen(false)
                  }}
                  initialFocus
                />
              </div>
            </PopoverContent>
          </Popover>
        </div>
      </div>

      <Separator className="my-6" />

      <div className="min-w-0 max-w-full">
        <div className="flex items-center gap-2 mb-3">
          <Tag className="h-4 w-4 text-muted-foreground shrink-0" />
          <Label className="text-sm font-medium">Type</Label>
        </div>
        <Popover open={typeDropdownOpen} onOpenChange={setTypeDropdownOpen}>
          <PopoverTrigger asChild>
            <Button variant="outline" className="w-full justify-between bg-transparent">
              <span className="truncate">
                {selectedCategories.length === 0 ? "Select types..." : `${selectedCategories.length} selected`}
              </span>
              <Tag className="h-4 w-4 ml-2 shrink-0" />
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-[280px] p-3" align="start">
            <div className="space-y-2 max-h-60 overflow-y-auto">
              {categoryOptions.map((option) => (
                <div
                  key={option.value}
                  className={`flex items-center gap-2 p-2 rounded cursor-pointer hover:bg-muted ${
                    selectedCategories.includes(option.value) ? "bg-muted" : ""
                  }`}
                  onClick={() => toggleCategory(option.value)}
                >
                  <div
                    className={`w-4 h-4 border-2 rounded flex items-center justify-center shrink-0 ${
                      selectedCategories.includes(option.value)
                        ? "bg-primary border-primary"
                        : "border-muted-foreground"
                    }`}
                  >
                    {selectedCategories.includes(option.value) && (
                      <CheckCircle2 className="h-3 w-3 text-primary-foreground" />
                    )}
                  </div>
                  <span className="text-sm truncate">{option.label}</span>
                </div>
              ))}
            </div>
          </PopoverContent>
        </Popover>
      </div>

      <Separator className="my-6" />

      <div className="min-w-0 max-w-full">
        <div className="flex items-center gap-2 mb-3">
          <CheckCircle2 className="h-4 w-4 text-muted-foreground shrink-0" />
          <Label className="text-sm font-medium">Action Status</Label>
        </div>
        <Popover open={actionStatusDropdownOpen} onOpenChange={setActionStatusDropdownOpen}>
          <PopoverTrigger asChild>
            <Button variant="outline" className="w-full justify-between bg-transparent">
              <span className="truncate">
                {selectedActionStatuses.length === 0
                  ? "Select statuses..."
                  : `${selectedActionStatuses.length} selected`}
              </span>
              <CheckCircle2 className="h-4 w-4 ml-2 shrink-0" />
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-[280px] p-3" align="start">
            <div className="space-y-2">
              <div
                className={`flex items-center gap-2 p-2 rounded cursor-pointer hover:bg-muted ${
                  selectedActionStatuses.includes("require-action") ? "bg-muted" : ""
                }`}
                onClick={() => toggleActionStatus("require-action")}
              >
                <div
                  className={`w-4 h-4 border-2 rounded flex items-center justify-center shrink-0 ${
                    selectedActionStatuses.includes("require-action")
                      ? "bg-primary border-primary"
                      : "border-muted-foreground"
                  }`}
                >
                  {selectedActionStatuses.includes("require-action") && (
                    <CheckCircle2 className="h-3 w-3 text-primary-foreground" />
                  )}
                </div>
                <span className="text-sm">Require Action</span>
              </div>
              <div
                className={`flex items-center gap-2 p-2 rounded cursor-pointer hover:bg-muted ${
                  selectedActionStatuses.includes("action-done") ? "bg-muted" : ""
                }`}
                onClick={() => toggleActionStatus("action-done")}
              >
                <div
                  className={`w-4 h-4 border-2 rounded flex items-center justify-center shrink-0 ${
                    selectedActionStatuses.includes("action-done")
                      ? "bg-primary border-primary"
                      : "border-muted-foreground"
                  }`}
                >
                  {selectedActionStatuses.includes("action-done") && (
                    <CheckCircle2 className="h-3 w-3 text-primary-foreground" />
                  )}
                </div>
                <span className="text-sm">Action Done</span>
              </div>
              <div
                className={`flex items-center gap-2 p-2 rounded cursor-pointer hover:bg-muted ${
                  selectedActionStatuses.includes("no-action-needed") ? "bg-muted" : ""
                }`}
                onClick={() => toggleActionStatus("no-action-needed")}
              >
                <div
                  className={`w-4 h-4 border-2 rounded flex items-center justify-center shrink-0 ${
                    selectedActionStatuses.includes("no-action-needed")
                      ? "bg-primary border-primary"
                      : "border-muted-foreground"
                  }`}
                >
                  {selectedActionStatuses.includes("no-action-needed") && (
                    <CheckCircle2 className="h-3 w-3 text-primary-foreground" />
                  )}
                </div>
                <span className="text-sm">No Action Needed</span>
              </div>
            </div>
          </PopoverContent>
        </Popover>
      </div>

      <Separator className="my-6" />

      <div className="flex items-center space-x-2 min-w-0 max-w-full">
        <Bell className="h-4 w-4 text-muted-foreground shrink-0" />
        <Checkbox
          id="needs-reminder"
          checked={needsReminder}
          onCheckedChange={(checked) => setNeedsReminder(checked as boolean)}
          className="shrink-0"
        />
        <Label htmlFor="needs-reminder" className="text-sm cursor-pointer truncate min-w-0">
          Has reminder
        </Label>
      </div>

      <Separator className="my-6" />

      <div className="flex items-center space-x-2 min-w-0 max-w-full">
        <Star className="h-4 w-4 text-muted-foreground shrink-0" />
        <Checkbox
          id="only-favorites"
          checked={onlyFavorites}
          onCheckedChange={(checked) => setOnlyFavorites(checked as boolean)}
          className="shrink-0"
        />
        <Label htmlFor="only-favorites" className="text-sm cursor-pointer truncate min-w-0">
          Favorites only
        </Label>
      </div>

      <div className="flex gap-2">
        <Button variant="outline" className="flex-1 bg-transparent" onClick={cancelFilters}>
          Cancel
        </Button>
        <Button className="flex-1" onClick={applyFilters} disabled={!filtersChanged}>
          Apply Filters
        </Button>
      </div>
    </div>
  )

  const hasActiveFilters =
    appliedCategories.length > 0 ||
    appliedActionStatuses.length > 0 ||
    appliedActionDueDateRange.from ||
    appliedActionDueDateRange.to ||
    appliedSentDateRange.from ||
    appliedSentDateRange.to ||
    appliedCreatedDateRange.from ||
    appliedCreatedDateRange.to ||
    appliedNeedsReminder ||
    appliedOnlyFavorites

  return (
    <div className="h-full flex flex-col w-full max-w-full min-w-0 overflow-hidden">
      <div className="p-4 flex items-center gap-3 border-b border-border/50 shrink-0 min-w-0 max-w-full overflow-hidden">
        <Image src="/logo.svg" alt="LetterON" width={32} height={32} className="shrink-0" />
        <h1 className="text-xl font-semibold truncate min-w-0 flex-1">LetterON</h1>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" className="shrink-0 rounded-full">
              <User className="h-5 w-5" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={onLogout}>
              <LogOut className="mr-2 h-4 w-4" />
              Logout
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      <div className="p-3 shrink-0 min-w-0 max-w-full overflow-hidden hidden md:block">
        <Button
          variant="default"
          size="lg"
          className="w-full max-w-full justify-start min-w-0 h-12"
          onClick={onCompose}
        >
          <PenSquare className="mr-2 h-5 w-5 shrink-0" />
          <span className="truncate min-w-0">Add New Letter Record</span>
        </Button>
      </div>

      <div className="px-3 pb-2 shrink-0 min-w-0 max-w-full overflow-hidden">
        <div className="flex gap-2 min-w-0 max-w-full">
          <div className="relative flex-1 min-w-0">
            <Input
              placeholder="Search emails..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="flex-1 bg-background/80 min-w-0 max-w-full pr-8"
            />
            {searchQuery && (
              <Button
                variant="ghost"
                size="icon"
                className="absolute right-0 top-0 h-full w-8 shrink-0"
                onClick={() => setSearchQuery("")}
              >
                <X className="h-4 w-4" />
              </Button>
            )}
          </div>
          <Button
            variant="outline"
            size="icon"
            onClick={() => setFilterOpen(!filterOpen)}
            className={`shrink-0 ${filterOpen ? "bg-accent" : ""}`}
          >
            <SlidersHorizontal className="h-4 w-4" />
          </Button>
        </div>

        {hasActiveFilters && (
          <div className="mt-2 flex flex-wrap gap-1.5">
            {appliedCategories.map((category) => {
              const display = getCategoryDisplay(category)
              return (
                <Badge key={category} variant="secondary" className="bg-gray-200 text-gray-700 pr-1 text-xs">
                  <span className="truncate">{display.label}</span>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-4 w-4 ml-1 p-0 hover:bg-transparent"
                    onClick={() => removeFilterChip("category", category)}
                  >
                    <X className="h-3 w-3" />
                  </Button>
                </Badge>
              )
            })}
            {appliedActionStatuses.map((status) => (
              <Badge key={status} variant="secondary" className="bg-gray-200 text-gray-700 pr-1 text-xs">
                <span className="truncate">
                  {status === "require-action"
                    ? "Require Action"
                    : status === "action-done"
                      ? "Action Done"
                      : "No Action"}
                </span>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-4 w-4 ml-1 p-0 hover:bg-transparent"
                  onClick={() => removeFilterChip("actionStatus", status)}
                >
                  <X className="h-3 w-3" />
                </Button>
              </Badge>
            ))}
            {(appliedActionDueDateRange.from || appliedActionDueDateRange.to) && (
              <Badge variant="secondary" className="bg-gray-200 text-gray-700 pr-1 text-xs">
                <span className="truncate">Action Due Date</span>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-4 w-4 ml-1 p-0 hover:bg-transparent"
                  onClick={() => removeFilterChip("actionDueDate")}
                >
                  <X className="h-3 w-3" />
                </Button>
              </Badge>
            )}
            {(appliedSentDateRange.from || appliedSentDateRange.to) && (
              <Badge variant="secondary" className="bg-gray-200 text-gray-700 pr-1 text-xs">
                <span className="truncate">Sent Date</span>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-4 w-4 ml-1 p-0 hover:bg-transparent"
                  onClick={() => removeFilterChip("sentDate")}
                >
                  <X className="h-3 w-3" />
                </Button>
              </Badge>
            )}
            {(appliedCreatedDateRange.from || appliedCreatedDateRange.to) && (
              <Badge variant="secondary" className="bg-gray-200 text-gray-700 pr-1 text-xs">
                <span className="truncate">Created Date</span>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-4 w-4 ml-1 p-0 hover:bg-transparent"
                  onClick={() => removeFilterChip("createdDate")}
                >
                  <X className="h-3 w-3" />
                </Button>
              </Badge>
            )}
            {appliedNeedsReminder && (
              <Badge variant="secondary" className="bg-gray-200 text-gray-700 pr-1 text-xs">
                <span className="truncate">Has Reminder</span>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-4 w-4 ml-1 p-0 hover:bg-transparent"
                  onClick={() => removeFilterChip("reminder")}
                >
                  <X className="h-3 w-3" />
                </Button>
              </Badge>
            )}
            {appliedOnlyFavorites && (
              <Badge variant="secondary" className="bg-gray-200 text-gray-700 pr-1 text-xs">
                <span className="truncate">Favorites</span>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-4 w-4 ml-1 p-0 hover:bg-transparent"
                  onClick={() => removeFilterChip("favorite")}
                >
                  <X className="h-3 w-3" />
                </Button>
              </Badge>
            )}
          </div>
        )}

        {/* Desktop filter panel */}
        {filterOpen && !isMobile && (
          <div className="mt-2 p-3 border rounded-lg bg-card min-w-0 max-w-full overflow-hidden">
            <FilterContent />
          </div>
        )}
      </div>

      {isMobile && (
        <Dialog open={filterOpen} onOpenChange={setFilterOpen}>
          <DialogContent className="max-h-[90vh] overflow-y-auto">
            <FilterContent />
          </DialogContent>
        </Dialog>
      )}

      <ScrollArea className="flex-1 min-w-0 max-w-full pb-20 md:pb-0">
        {filteredEmails.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-muted-foreground p-4">
            <p className="text-center break-words">
              No Letter Record found, click "Add New Letter Record" to create one from post letter image :)
            </p>
          </div>
        ) : (
          <div className="w-full max-w-full overflow-hidden">
            {filteredEmails.map((email) => (
              <EmailListItem
                key={email.id}
                email={email}
                isSelected={selectedEmail?.id === email.id}
                onSelect={() => onSelectEmail(email)}
                onArchive={() => onArchiveEmail(email.id)}
                onDelete={() => onDeleteEmail(email.id)}
                onSnooze={onSnoozeEmail}
              />
            ))}
          </div>
        )}
      </ScrollArea>
    </div>
  )
}

interface EmailListItemProps {
  email: Email
  isSelected: boolean
  onSelect: () => void
  onArchive: () => void
  onDelete: () => void
  onSnooze: (id: string, snoozeUntil: Date) => void
}

function EmailListItem({ email, isSelected, onSelect, onArchive, onDelete, onSnooze }: EmailListItemProps) {
  const [isHovered, setIsHovered] = useState(false)
  const itemRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (isSelected && itemRef.current) {
      itemRef.current.scrollIntoView({ behavior: "smooth", block: "nearest" })
    }
  }, [isSelected])

  const categoryDisplay = getCategoryDisplay(email.letterCategory)

  const getActionStatusBadge = (status?: ActionStatus) => {
    if (!status) return null

    const displays = {
      "require-action": { label: "Require Action", color: "bg-red-100 text-red-700" },
      "action-done": { label: "Action Done", color: "bg-gray-100 text-gray-700" },
      "no-action-needed": { label: "No Action", color: "bg-gray-100 text-gray-700" },
    }

    return displays[status]
  }

  const actionBadge = getActionStatusBadge(email.actionStatus)

  return (
    <div
      ref={itemRef}
      className={`block w-full p-3 cursor-pointer relative min-w-0 border-b border-border/50 ${
        isSelected
          ? "bg-primary/10 border-l-4 border-primary shadow-sm"
          : isHovered
            ? "bg-muted/50 border-l-4 border-transparent"
            : "border-l-4 border-transparent"
      } ${!email.read ? "font-medium" : ""}`}
      onClick={onSelect}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div className="flex items-start gap-3 w-full min-w-0">
        <div className={`shrink-0 w-10 h-10 rounded-lg flex items-center justify-center ${categoryDisplay.color}`}>
          {categoryDisplay.icon}
        </div>

        <div className="flex-1 min-w-0 w-0">
          <div className="flex items-start justify-between gap-2 mb-1 w-full min-w-0">
            <div className="flex-1 min-w-0">
              <div className="text-sm truncate">{email.subject}</div>
              <div className="text-sm text-muted-foreground truncate">from {email.sender.name}</div>
            </div>
            <div className="flex items-center gap-1 shrink-0">
              {email.flagged && <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />}
              <div className="text-xs text-muted-foreground whitespace-nowrap">
                {formatDistanceToNow(new Date(email.date))}
              </div>
            </div>
          </div>

          <div className="text-xs text-muted-foreground truncate mb-2 w-full">{email.content.substring(0, 100)}...</div>

          <div className="flex flex-wrap gap-1.5 w-full">
            <Badge variant="outline" className="text-xs px-1.5 py-0 shrink-0 bg-white border-gray-300">
              <span className="truncate">{categoryDisplay.label}</span>
            </Badge>

            {actionBadge && (
              <Badge variant="outline" className={`text-xs px-1.5 py-0 shrink-0 ${actionBadge.color}`}>
                <span className="truncate">{actionBadge.label}</span>
              </Badge>
            )}

            {email.hasReminder && (
              <Badge variant="outline" className="text-xs px-1.5 py-0 shrink-0 bg-yellow-100 text-yellow-700">
                <Bell className="h-3 w-3 mr-1 shrink-0" />
                <span className="truncate">Reminder</span>
              </Badge>
            )}
          </div>
        </div>
      </div>

      {isHovered && (
        <div className="absolute right-2 top-1/2 -translate-y-1/2 flex gap-1 bg-background/95 backdrop-blur-sm px-1 py-0.5 rounded-md shadow-md border">
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7 shrink-0"
            onClick={(e) => {
              e.stopPropagation()
              onArchive()
            }}
          >
            <Archive className="h-3.5 w-3.5" />
          </Button>

          <Popover>
            <PopoverTrigger asChild>
              <Button variant="ghost" size="icon" className="h-7 w-7 shrink-0" onClick={(e) => e.stopPropagation()}>
                <Clock className="h-3.5 w-3.5" />
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-auto p-0" align="end">
              <div className="p-2">
                <div className="font-medium mb-2">Snooze until</div>
                <div className="space-y-1">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="w-full justify-start"
                    onClick={(e) => {
                      e.stopPropagation()
                      const tomorrow = new Date()
                      tomorrow.setDate(tomorrow.getDate() + 1)
                      tomorrow.setHours(9, 0, 0, 0)
                      onSnooze(email.id, tomorrow)
                    }}
                  >
                    Tomorrow morning
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="w-full justify-start"
                    onClick={(e) => {
                      e.stopPropagation()
                      const nextWeek = new Date()
                      nextWeek.setDate(nextWeek.getDate() + 7)
                      nextWeek.setHours(9, 0, 0, 0)
                      onSnooze(email.id, nextWeek)
                    }}
                  >
                    Next week
                  </Button>
                </div>
                <Calendar
                  mode="single"
                  selected={undefined}
                  onSelect={(date) => {
                    if (date) {
                      onSnooze(email.id, date)
                    }
                  }}
                  className="mt-2"
                />
              </div>
            </PopoverContent>
          </Popover>

          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7 shrink-0"
            onClick={(e) => {
              e.stopPropagation()
              onDelete()
            }}
          >
            <Trash2 className="h-3.5 w-3.5" />
          </Button>
        </div>
      )}
    </div>
  )
}
