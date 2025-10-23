"use client"

import type React from "react"
import { useState, useRef } from "react"
import { X, Upload, Trash2, ImageIcon } from "lucide-react"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { useToast } from "@/hooks/use-toast"
import type { Email, LetterCategory, ActionStatus } from "@/types/email"
import { Badge } from "@/components/ui/badge"
import { getCategoryDisplay } from "@/lib/letter-categories"
import { Checkbox } from "@/components/ui/checkbox"
import { TokenStorage } from "@/lib/token-storage"


interface UploadLettersProps {
  onClose: () => void
  onCreateLetter: (letter: Email) => void
}

interface LetterImage {
  file: File
  preview: string
}

interface ImageProcessResponse {
  letter_id: string
  subject: string
  sender: string
  content: string
  letterCategory: LetterCategory
  actionStatus: ActionStatus
  hasReminder: boolean
  actionDueDate?: string
  aiSuggestion: string
  originalImages: string[]
}

export default function UploadLetters({ onClose, onCreateLetter }: UploadLettersProps) {
  const [images, setImages] = useState<LetterImage[]>([])
  const [uploading, setUploading] = useState(false)
  const [previewModalOpen, setPreviewModalOpen] = useState(false)
  const [apiResponse, setApiResponse] = useState<ImageProcessResponse | null>(null)
  const [includeTranslation, setIncludeTranslation] = useState(false)
  const [translationLanguage, setTranslationLanguage] = useState("")
  const fileInputRef = useRef<HTMLInputElement>(null)
  const { toast } = useToast()

  const MAX_IMAGES = 3
  const MAX_FILE_SIZE = 1024 * 1024 // 1MB in bytes
  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const newFiles = Array.from(e.target.files)

      const validFiles = newFiles.filter((file) => {
        if (file.size > MAX_FILE_SIZE) {
          toast({
            title: "File Too Large",
            description: `${file.name} exceeds 1MB limit`,
            variant: "destructive",
          })
          return false
        }
        if (!file.type.startsWith("image/")) {
          toast({
            title: "Invalid File Type",
            description: `${file.name} is not an image`,
            variant: "destructive",
          })
          return false
        }
        return true
      })

      if (images.length + validFiles.length > MAX_IMAGES) {
        toast({
          title: "Too Many Images",
          description: `You can only upload up to ${MAX_IMAGES} images`,
          variant: "destructive",
        })
        return
      }

      const newImages = validFiles.map((file) => ({
        file,
        preview: URL.createObjectURL(file),
      }))

      setImages([...images, ...newImages])
    }
  }

  const handleRemoveImage = (index: number) => {
    const newImages = [...images]
    URL.revokeObjectURL(newImages[index].preview)
    newImages.splice(index, 1)
    setImages(newImages)
  }

  const handleUpload = async () => {
    if (images.length === 0) return

    setUploading(true)

    try {
      // Create FormData
      const formData = new FormData()

      // Append all image files
      images.forEach((image) => {
        formData.append("files", image.file)
      })

      // Append translation options
      formData.append("include_translation", includeTranslation.toString())
      if (includeTranslation && translationLanguage) {
        formData.append("translation_language", translationLanguage)
      }

      // Get JWT token from localStorage or your auth provider
      const token = TokenStorage.getToken() // Adjust based on your auth implementation
      // Call the API
      const response = await fetch(`${API_BASE_URL}/letters/process-images`, {
        method: "POST",
        headers: {
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: "Unknown error" }))
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
      }

      const result: ImageProcessResponse = await response.json()

      setApiResponse(result)
      setPreviewModalOpen(true)

      toast({
        title: "Processing Complete",
        description: "Letter has been analyzed successfully.",
      })
    } catch (error) {
      console.error("Upload error:", error)
      toast({
        title: "Upload Failed",
        description: error instanceof Error ? error.message : "Failed to process images. Please try again.",
        variant: "destructive",
      })
      setUploading(false)
    } finally {
      setUploading(false)
    }
  }

  const handleConfirmCreate = () => {
    if (!apiResponse) return

    const newLetter: Email = {
      id: apiResponse.letter_id,
      subject: apiResponse.subject,
      sender: {
        name: apiResponse.sender,
        email: `${apiResponse.sender.toLowerCase().replace(/\s+/g, "")}@example.com`,
      },
      recipients: [],
      content: apiResponse.content,
      date: new Date().toISOString(),
      read: false,
      flagged: false,
      snoozed: false,
      archived: false,
      deleted: false,
      account: "main",
      letterCategory: apiResponse.letterCategory,
      actionStatus: apiResponse.actionStatus,
      hasReminder: apiResponse.hasReminder,
      actionDueDate: apiResponse.actionDueDate,
      recordCreatedAt: new Date().toISOString(),
      originalImages: apiResponse.originalImages,
      aiSuggestion: apiResponse.aiSuggestion,
    }

    onCreateLetter(newLetter)

    // Clean up
    images.forEach((img) => URL.revokeObjectURL(img.preview))
    setImages([])
    setApiResponse(null)
    setPreviewModalOpen(false)
    setIncludeTranslation(false)
    setTranslationLanguage("")

    toast({
      title: "Letter Created",
      description: "Your letter has been successfully created.",
    })

    onClose()
  }

  const categoryDisplay = apiResponse ? getCategoryDisplay(apiResponse.letterCategory) : null

  return (
    <div className="h-full flex flex-col bg-background">
      <div className="p-4 flex items-center justify-between border-b border-border/50">
        <h2 className="text-lg font-medium">Upload Letter Images</h2>
        <Button variant="ghost" size="icon" onClick={onClose}>
          <X className="h-5 w-5" />
        </Button>
      </div>

      <ScrollArea className="flex-1 p-4 md:p-6">
        <div className="max-w-2xl mx-auto space-y-6">
          {/* Translation Options - Show before upload */}
          <div className="border rounded-lg p-4 space-y-3">
            <div className="flex items-center space-x-2">
              <Checkbox
                id="include-translation-upload"
                checked={includeTranslation}
                onCheckedChange={(checked) => setIncludeTranslation(checked as boolean)}
              />
              <Label htmlFor="include-translation-upload" className="cursor-pointer">
                Include translation
              </Label>
            </div>

            {includeTranslation && (
              <div>
                <Label>Translation Language</Label>
                <Select value={translationLanguage} onValueChange={setTranslationLanguage}>
                  <SelectTrigger className="mt-1">
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
            )}
          </div>

          <div
            className="border-2 border-dashed border-border rounded-lg p-8 md:p-12 text-center cursor-pointer hover:border-primary/50 transition-colors"
            onClick={() => fileInputRef.current?.click()}
          >
            <ImageIcon className="h-10 w-10 md:h-12 md:w-12 mx-auto mb-4 text-muted-foreground" />
            <h3 className="text-base md:text-lg font-medium mb-2">Upload Letter Images</h3>
            <p className="text-sm text-muted-foreground mb-4">Click to select images or drag and drop</p>
            <p className="text-xs text-muted-foreground">Maximum {MAX_IMAGES} images, each up to 1MB</p>
            <p className="text-xs text-muted-foreground mt-1">
              {images.length} / {MAX_IMAGES} images selected
            </p>
          </div>

          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileSelect}
            className="hidden"
            accept="image/*"
            multiple
          />

          {images.length > 0 && (
            <div className="space-y-4">
              <h3 className="font-medium">Selected Images</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {images.map((image, index) => (
                  <div key={index} className="relative group border rounded-lg overflow-hidden">
                    <img
                      src={image.preview || "/placeholder.svg"}
                      alt={`Letter ${index + 1}`}
                      className="w-full h-48 md:h-64 object-cover"
                    />
                    <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                      <Button variant="destructive" size="icon" onClick={() => handleRemoveImage(index)}>
                        <Trash2 className="h-5 w-5" />
                      </Button>
                    </div>
                    <div className="absolute bottom-0 left-0 right-0 bg-black/70 text-white p-2 text-xs">
                      <p className="truncate">{image.file.name}</p>
                      <p className="text-muted-foreground">{(image.file.size / 1024).toFixed(0)} KB</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </ScrollArea>

      <div className="p-4 border-t border-border/50 flex items-center justify-between">
        <Button variant="outline" onClick={onClose}>
          Cancel
        </Button>
        <Button
          onClick={handleUpload}
          disabled={images.length === 0 || uploading || (includeTranslation && !translationLanguage)}
        >
          <Upload className="h-4 w-4 mr-2" />
          {uploading ? "Processing..." : `Upload ${images.length} Image${images.length !== 1 ? "s" : ""}`}
        </Button>
      </div>

      <Dialog open={previewModalOpen} onOpenChange={setPreviewModalOpen}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Preview Letter Information</DialogTitle>
          </DialogHeader>
          {apiResponse && (
            <div className="space-y-4">
              <div>
                <Label>Letter ID</Label>
                <Input value={apiResponse.letter_id} readOnly className="mt-1 font-mono text-sm" />
              </div>

              <div>
                <Label>Subject</Label>
                <Input value={apiResponse.subject} readOnly className="mt-1" />
              </div>

              <div>
                <Label>Sender</Label>
                <Input value={apiResponse.sender} readOnly className="mt-1" />
              </div>

              <div>
                <Label>Type</Label>
                <div className="mt-1">
                  {categoryDisplay && (
                    <Badge variant="outline" className={categoryDisplay.color}>
                      {categoryDisplay.label}
                    </Badge>
                  )}
                </div>
              </div>

              <div>
                <Label>Action Status</Label>
                <div className="mt-1">
                  <Badge
                    variant="outline"
                    className={
                      apiResponse.actionStatus === "require-action"
                        ? "bg-red-100 text-red-700"
                        : apiResponse.actionStatus === "action-done"
                          ? "bg-green-100 text-green-700"
                          : "bg-gray-100 text-gray-700"
                    }
                  >
                    {apiResponse.actionStatus === "require-action"
                      ? "Require Action"
                      : apiResponse.actionStatus === "action-done"
                        ? "Action Done"
                        : "No Action Needed"}
                  </Badge>
                </div>
              </div>

              <div>
                <Label>Reminder</Label>
                <div className="mt-1">
                  <Badge variant="outline" className={apiResponse.hasReminder ? "bg-yellow-100 text-yellow-700" : ""}>
                    {apiResponse.hasReminder ? "Active" : "None"}
                  </Badge>
                </div>
              </div>

              {apiResponse.actionDueDate && (
                <div>
                  <Label>Action Due Date</Label>
                  <Input value={apiResponse.actionDueDate} readOnly className="mt-1" />
                </div>
              )}

              <div>
                <Label>Content (OCR Extracted)</Label>
                <Textarea value={apiResponse.content} readOnly className="mt-1 min-h-[120px]" />
              </div>

              <div>
                <Label>AI Suggestion</Label>
                <Textarea value={apiResponse.aiSuggestion} readOnly className="mt-1 min-h-[80px]" />
              </div>

              {apiResponse.originalImages.length > 0 && (
                <div>
                  <Label>Uploaded Images</Label>
                  <div className="mt-2 grid grid-cols-3 gap-2">
                    {apiResponse.originalImages.map((url, index) => (
                      <img
                        key={index}
                        src={url}
                        alt={`Uploaded ${index + 1}`}
                        className="w-full h-24 object-cover rounded border"
                      />
                    ))}
                  </div>
                </div>
              )}

              <div className="flex justify-end gap-2 pt-4 border-t">
                <Button variant="outline" onClick={() => setPreviewModalOpen(false)}>
                  Cancel
                </Button>
                <Button onClick={handleConfirmCreate}>Confirm & Create</Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}