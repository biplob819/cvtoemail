import { useEffect, useState, useCallback, useRef } from 'react';
import {
  Upload,
  Save,
  Eye,
  Plus,
  Trash2,
  GripVertical,
  X,
  FileText,
  AlertCircle,
} from 'lucide-react';
import { Card, Button, Input, Modal, Skeleton, showToast } from '../components/ui';
import { getCV, updateCV, uploadCV, getPreviewUrl } from '../api';
import type { CVData, PersonalInfo, WorkExperience, Education, Certification } from '../types';

// ---- Empty defaults ----
const emptyPersonalInfo: PersonalInfo = {
  name: '', email: '', phone: '', location: '', linkedin: '', website: '',
};
const emptyWorkExp: WorkExperience = { title: '', company: '', duration: '', achievements: [''] };
const emptyEducation: Education = { degree: '', institution: '', year: '', details: '' };
const emptyCertification: Certification = { name: '', issuer: '', year: '' };

export default function CVEditor() {
  const [cv, setCV] = useState<CVData | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [showOverwriteModal, setShowOverwriteModal] = useState(false);
  const [parseError, setParseError] = useState<string | null>(null);
  const pendingFileRef = useRef<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Load existing CV
  useEffect(() => {
    getCV()
      .then((data) => {
        if (data && data.id) {
          setCV(data);
        } else {
          // No CV yet, start with empty
          setCV(null);
        }
      })
      .catch(() => setCV(null))
      .finally(() => setLoading(false));
  }, []);

  // File upload handler
  const handleFileUpload = useCallback(async (file: File) => {
    // Validate
    const ext = file.name.toLowerCase();
    if (!ext.endsWith('.pdf') && !ext.endsWith('.docx')) {
      showToast('Only PDF and DOCX files are supported', 'error');
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      showToast('File size exceeds 5MB limit', 'error');
      return;
    }

    // Check if CV exists -> confirm overwrite
    if (cv && cv.id) {
      pendingFileRef.current = file;
      setShowOverwriteModal(true);
      return;
    }

    await doUpload(file);
  }, [cv]);

  const doUpload = async (file: File) => {
    setUploading(true);
    setParseError(null);
    try {
      const data = await uploadCV(file);
      setCV(data);
      showToast('CV uploaded and parsed successfully!', 'success');
    } catch (err: any) {
      const msg = err?.response?.data?.detail || 'Failed to upload CV';
      setParseError(msg);
      showToast(msg, 'error');
    } finally {
      setUploading(false);
      setShowOverwriteModal(false);
      pendingFileRef.current = null;
    }
  };

  const confirmOverwrite = () => {
    if (pendingFileRef.current) {
      doUpload(pendingFileRef.current);
    }
  };

  // Drag and drop
  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      const file = e.dataTransfer.files[0];
      if (file) handleFileUpload(file);
    },
    [handleFileUpload]
  );

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  // Save handler
  const handleSave = async () => {
    if (!cv) return;
    setSaving(true);
    try {
      const updated = await updateCV(cv);
      setCV(updated);
      showToast('CV saved successfully!', 'success');
    } catch (err: any) {
      showToast(err?.response?.data?.detail || 'Failed to save CV', 'error');
    } finally {
      setSaving(false);
    }
  };

  // Field updaters
  const updatePersonalInfo = (field: keyof PersonalInfo, value: string) => {
    setCV((prev) => prev ? { ...prev, personal_info: { ...prev.personal_info, [field]: value } } : prev);
  };

  const updateSummary = (value: string) => {
    setCV((prev) => prev ? { ...prev, summary: value } : prev);
  };

  // Work experience
  const addWorkExp = () => {
    setCV((prev) => prev ? { ...prev, work_experience: [...prev.work_experience, { ...emptyWorkExp }] } : prev);
  };

  const removeWorkExp = (index: number) => {
    setCV((prev) => prev ? { ...prev, work_experience: prev.work_experience.filter((_, i) => i !== index) } : prev);
  };

  const updateWorkExp = (index: number, field: keyof WorkExperience, value: any) => {
    setCV((prev) => {
      if (!prev) return prev;
      const updated = [...prev.work_experience];
      updated[index] = { ...updated[index], [field]: value };
      return { ...prev, work_experience: updated };
    });
  };

  const addAchievement = (expIdx: number) => {
    setCV((prev) => {
      if (!prev) return prev;
      const updated = [...prev.work_experience];
      updated[expIdx] = { ...updated[expIdx], achievements: [...updated[expIdx].achievements, ''] };
      return { ...prev, work_experience: updated };
    });
  };

  const removeAchievement = (expIdx: number, achIdx: number) => {
    setCV((prev) => {
      if (!prev) return prev;
      const updated = [...prev.work_experience];
      updated[expIdx] = {
        ...updated[expIdx],
        achievements: updated[expIdx].achievements.filter((_, i) => i !== achIdx),
      };
      return { ...prev, work_experience: updated };
    });
  };

  const updateAchievement = (expIdx: number, achIdx: number, value: string) => {
    setCV((prev) => {
      if (!prev) return prev;
      const updated = [...prev.work_experience];
      const achs = [...updated[expIdx].achievements];
      achs[achIdx] = value;
      updated[expIdx] = { ...updated[expIdx], achievements: achs };
      return { ...prev, work_experience: updated };
    });
  };

  // Education
  const addEducation = () => {
    setCV((prev) => prev ? { ...prev, education: [...prev.education, { ...emptyEducation }] } : prev);
  };

  const removeEducation = (index: number) => {
    setCV((prev) => prev ? { ...prev, education: prev.education.filter((_, i) => i !== index) } : prev);
  };

  const updateEducation = (index: number, field: keyof Education, value: string) => {
    setCV((prev) => {
      if (!prev) return prev;
      const updated = [...prev.education];
      updated[index] = { ...updated[index], [field]: value };
      return { ...prev, education: updated };
    });
  };

  // Skills (tag-style)
  const [skillInput, setSkillInput] = useState('');

  const addSkill = () => {
    const trimmed = skillInput.trim();
    if (!trimmed || !cv) return;
    if (cv.skills.includes(trimmed)) {
      showToast('Skill already added', 'info');
      return;
    }
    setCV({ ...cv, skills: [...cv.skills, trimmed] });
    setSkillInput('');
  };

  const removeSkill = (index: number) => {
    setCV((prev) => prev ? { ...prev, skills: prev.skills.filter((_, i) => i !== index) } : prev);
  };

  // Certifications
  const addCertification = () => {
    setCV((prev) => prev ? { ...prev, certifications: [...prev.certifications, { ...emptyCertification }] } : prev);
  };

  const removeCertification = (index: number) => {
    setCV((prev) => prev ? { ...prev, certifications: prev.certifications.filter((_, i) => i !== index) } : prev);
  };

  const updateCertification = (index: number, field: keyof Certification, value: string) => {
    setCV((prev) => {
      if (!prev) return prev;
      const updated = [...prev.certifications];
      updated[index] = { ...updated[index], [field]: value };
      return { ...prev, certifications: updated };
    });
  };

  // Enter manual mode (no upload)
  const startManualEntry = () => {
    setCV({
      personal_info: { ...emptyPersonalInfo },
      summary: '',
      work_experience: [],
      education: [],
      skills: [],
      certifications: [],
    });
    setParseError(null);
  };

  // --- RENDER ---

  if (loading) {
    return (
      <div>
        <Skeleton height={32} width={200} className="mb-6" />
        <Skeleton height={200} className="rounded-lg mb-4" />
        <Skeleton height={300} className="rounded-lg" />
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-text">CV Editor</h1>
        <div className="flex items-center gap-2">
          {cv && cv.id && (
            <a href={getPreviewUrl()} target="_blank" rel="noopener noreferrer">
              <Button variant="secondary" className="gap-2 text-sm">
                <Eye className="size-4" /> Preview PDF
              </Button>
            </a>
          )}
          {cv && (
            <Button onClick={handleSave} loading={saving} className="gap-2 text-sm">
              <Save className="size-4" /> Save
            </Button>
          )}
        </div>
      </div>

      {/* Upload Zone */}
      {uploading ? (
        <Card className="mb-6">
          <div className="flex flex-col items-center py-8">
            <Skeleton height={24} width={24} className="rounded-full mb-3" />
            <p className="text-sm text-text-muted">Parsing your CV with AI...</p>
            <div className="w-48 mt-4">
              <Skeleton height={8} className="rounded-full" />
            </div>
          </div>
        </Card>
      ) : (
        <Card className="mb-6">
          <div
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onClick={() => fileInputRef.current?.click()}
            className="flex flex-col items-center py-8 border-2 border-dashed border-border rounded-lg
                       cursor-pointer hover:border-primary/40 hover:bg-primary/5 transition-colors"
          >
            <Upload className="size-8 text-text-muted mb-3" />
            <p className="text-sm font-medium text-text mb-1">
              {cv ? 'Re-upload CV' : 'Upload your CV'}
            </p>
            <p className="text-xs text-text-muted">
              Drag & drop or click to browse. PDF or DOCX, max 5MB.
            </p>
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.docx"
              className="hidden"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) handleFileUpload(file);
                e.target.value = '';
              }}
            />
          </div>
        </Card>
      )}

      {/* Parse error */}
      {parseError && (
        <Card className="mb-6 !border-danger/30 !bg-danger/5">
          <div className="flex items-start gap-3">
            <AlertCircle className="size-5 text-danger shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm font-medium text-danger mb-1">Parse Failed</p>
              <p className="text-sm text-text-muted">{parseError}</p>
              <Button
                variant="secondary"
                className="mt-3 text-sm"
                onClick={startManualEntry}
              >
                Enter data manually
              </Button>
            </div>
          </div>
        </Card>
      )}

      {/* No CV yet */}
      {!cv && !parseError && (
        <Card>
          <div className="flex flex-col items-center py-12 text-center">
            <FileText className="size-10 text-border mb-3" />
            <p className="text-sm text-text-muted mb-4">
              Upload a CV to get started, or enter your information manually.
            </p>
            <Button variant="secondary" onClick={startManualEntry} className="text-sm">
              Enter Manually
            </Button>
          </div>
        </Card>
      )}

      {/* CV Editor Form */}
      {cv && (
        <div className="space-y-6">
          {/* Personal Info */}
          <Card>
            <h2 className="text-base font-semibold text-text mb-4">Personal Information</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Input label="Full Name" value={cv.personal_info.name} onChange={(e) => updatePersonalInfo('name', e.target.value)} />
              <Input label="Email" type="email" value={cv.personal_info.email} onChange={(e) => updatePersonalInfo('email', e.target.value)} />
              <Input label="Phone" value={cv.personal_info.phone} onChange={(e) => updatePersonalInfo('phone', e.target.value)} />
              <Input label="Location" value={cv.personal_info.location} onChange={(e) => updatePersonalInfo('location', e.target.value)} />
              <Input label="LinkedIn" value={cv.personal_info.linkedin || ''} onChange={(e) => updatePersonalInfo('linkedin', e.target.value)} />
              <Input label="Website" value={cv.personal_info.website || ''} onChange={(e) => updatePersonalInfo('website', e.target.value)} />
            </div>
          </Card>

          {/* Summary */}
          <Card>
            <h2 className="text-base font-semibold text-text mb-4">Professional Summary</h2>
            <textarea
              value={cv.summary}
              onChange={(e) => updateSummary(e.target.value)}
              rows={4}
              className="w-full px-3 py-2.5 rounded-lg border border-border bg-bg text-text
                         placeholder:text-text-muted focus:outline-none focus:ring-2
                         focus:ring-primary focus:ring-offset-1 resize-y text-sm"
              placeholder="A brief professional summary..."
            />
          </Card>

          {/* Work Experience */}
          <Card>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-semibold text-text">Work Experience</h2>
              <Button variant="secondary" onClick={addWorkExp} className="text-sm gap-1.5">
                <Plus className="size-4" /> Add
              </Button>
            </div>
            {cv.work_experience.length === 0 && (
              <p className="text-sm text-text-muted py-4 text-center">No work experience added yet.</p>
            )}
            <div className="space-y-4">
              {cv.work_experience.map((exp, idx) => (
                <div key={idx} className="border border-border rounded-lg p-4 relative group">
                  <button
                    onClick={() => removeWorkExp(idx)}
                    className="absolute top-3 right-3 p-1 rounded-md text-text-muted hover:text-danger hover:bg-danger/10 transition-colors opacity-0 group-hover:opacity-100"
                  >
                    <Trash2 className="size-4" />
                  </button>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-3">
                    <Input label="Title" value={exp.title} onChange={(e) => updateWorkExp(idx, 'title', e.target.value)} />
                    <Input label="Company" value={exp.company} onChange={(e) => updateWorkExp(idx, 'company', e.target.value)} />
                    <Input label="Duration" value={exp.duration} onChange={(e) => updateWorkExp(idx, 'duration', e.target.value)} placeholder="e.g. Jan 2020 - Present" />
                  </div>
                  <div className="mt-3">
                    <div className="flex items-center justify-between mb-2">
                      <label className="text-sm font-medium text-text">Achievements</label>
                      <button
                        onClick={() => addAchievement(idx)}
                        className="text-xs text-primary hover:text-primary-hover font-medium flex items-center gap-1"
                      >
                        <Plus className="size-3" /> Add bullet
                      </button>
                    </div>
                    {exp.achievements.map((ach, achIdx) => (
                      <div key={achIdx} className="flex items-start gap-2 mb-2">
                        <GripVertical className="size-4 text-text-muted mt-2.5 shrink-0" />
                        <input
                          value={ach}
                          onChange={(e) => updateAchievement(idx, achIdx, e.target.value)}
                          className="flex-1 h-9 px-3 rounded-md border border-border bg-bg text-sm text-text
                                     focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-1"
                          placeholder="Achievement or responsibility..."
                        />
                        <button
                          onClick={() => removeAchievement(idx, achIdx)}
                          className="p-1.5 rounded-md text-text-muted hover:text-danger hover:bg-danger/10 transition-colors mt-0.5"
                        >
                          <X className="size-3.5" />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </Card>

          {/* Education */}
          <Card>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-semibold text-text">Education</h2>
              <Button variant="secondary" onClick={addEducation} className="text-sm gap-1.5">
                <Plus className="size-4" /> Add
              </Button>
            </div>
            {cv.education.length === 0 && (
              <p className="text-sm text-text-muted py-4 text-center">No education added yet.</p>
            )}
            <div className="space-y-4">
              {cv.education.map((edu, idx) => (
                <div key={idx} className="border border-border rounded-lg p-4 relative group">
                  <button
                    onClick={() => removeEducation(idx)}
                    className="absolute top-3 right-3 p-1 rounded-md text-text-muted hover:text-danger hover:bg-danger/10 transition-colors opacity-0 group-hover:opacity-100"
                  >
                    <Trash2 className="size-4" />
                  </button>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    <Input label="Degree" value={edu.degree} onChange={(e) => updateEducation(idx, 'degree', e.target.value)} />
                    <Input label="Institution" value={edu.institution} onChange={(e) => updateEducation(idx, 'institution', e.target.value)} />
                    <Input label="Year" value={edu.year} onChange={(e) => updateEducation(idx, 'year', e.target.value)} placeholder="e.g. 2020" />
                  </div>
                </div>
              ))}
            </div>
          </Card>

          {/* Skills */}
          <Card>
            <h2 className="text-base font-semibold text-text mb-4">Skills</h2>
            <div className="flex flex-wrap gap-2 mb-3">
              {cv.skills.map((skill, idx) => (
                <span
                  key={idx}
                  className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-primary/10 text-primary text-sm font-medium"
                >
                  {skill}
                  <button
                    onClick={() => removeSkill(idx)}
                    className="hover:text-danger transition-colors"
                  >
                    <X className="size-3.5" />
                  </button>
                </span>
              ))}
              {cv.skills.length === 0 && (
                <p className="text-sm text-text-muted">No skills added yet.</p>
              )}
            </div>
            <div className="flex gap-2">
              <input
                value={skillInput}
                onChange={(e) => setSkillInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    addSkill();
                  }
                }}
                className="flex-1 h-9 px-3 rounded-md border border-border bg-bg text-sm text-text
                           focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-1"
                placeholder="Type a skill and press Enter..."
              />
              <Button variant="secondary" onClick={addSkill} className="text-sm">
                Add
              </Button>
            </div>
          </Card>

          {/* Certifications */}
          <Card>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-semibold text-text">Certifications</h2>
              <Button variant="secondary" onClick={addCertification} className="text-sm gap-1.5">
                <Plus className="size-4" /> Add
              </Button>
            </div>
            {cv.certifications.length === 0 && (
              <p className="text-sm text-text-muted py-4 text-center">No certifications added yet.</p>
            )}
            <div className="space-y-4">
              {cv.certifications.map((cert, idx) => (
                <div key={idx} className="border border-border rounded-lg p-4 relative group">
                  <button
                    onClick={() => removeCertification(idx)}
                    className="absolute top-3 right-3 p-1 rounded-md text-text-muted hover:text-danger hover:bg-danger/10 transition-colors opacity-0 group-hover:opacity-100"
                  >
                    <Trash2 className="size-4" />
                  </button>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    <Input label="Name" value={cert.name} onChange={(e) => updateCertification(idx, 'name', e.target.value)} />
                    <Input label="Issuer" value={cert.issuer || ''} onChange={(e) => updateCertification(idx, 'issuer', e.target.value)} />
                    <Input label="Year" value={cert.year || ''} onChange={(e) => updateCertification(idx, 'year', e.target.value)} />
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>
      )}

      {/* Overwrite confirmation modal */}
      <Modal
        open={showOverwriteModal}
        onClose={() => {
          setShowOverwriteModal(false);
          pendingFileRef.current = null;
        }}
        title="Replace Existing CV?"
      >
        <p className="text-sm text-text-muted mb-6">
          You already have a CV saved. Uploading a new file will replace all existing data. This action cannot be undone.
        </p>
        <div className="flex justify-end gap-3">
          <Button
            variant="secondary"
            onClick={() => {
              setShowOverwriteModal(false);
              pendingFileRef.current = null;
            }}
          >
            Cancel
          </Button>
          <Button variant="danger" onClick={confirmOverwrite} loading={uploading}>
            Replace CV
          </Button>
        </div>
      </Modal>
    </div>
  );
}
