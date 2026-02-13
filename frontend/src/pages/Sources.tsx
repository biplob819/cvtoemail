import { useState, useEffect, useCallback } from "react";
import {
  Globe,
  Plus,
  Trash2,
  Pencil,
  Play,
  Pause,
  RefreshCw,
  ExternalLink,
  Search,
  AlertCircle,
} from "lucide-react";
import {
  Card,
  Button,
  Input,
  Badge,
  Modal,
  Table,
  TableHeader,
  TableRow,
  TableCell,
  Skeleton,
  showToast,
} from "../components/ui";
import {
  getSources,
  createSource,
  updateSource,
  deleteSource,
  scanSource,
} from "../api";
import type { JobSource, JobSourceCreate } from "../types";

// ---------------------------------------------------------------------------
// Add / Edit Source Modal
// ---------------------------------------------------------------------------

interface SourceFormProps {
  open: boolean;
  onClose: () => void;
  onSaved: () => void;
  editSource?: JobSource | null;
}

function SourceFormModal({ open, onClose, onSaved, editSource }: SourceFormProps) {
  const [url, setUrl] = useState("");
  const [portalName, setPortalName] = useState("");
  const [filtersDescription, setFiltersDescription] = useState("");
  const [saving, setSaving] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const isEdit = !!editSource;

  useEffect(() => {
    if (open) {
      if (editSource) {
        setUrl(editSource.url);
        setPortalName(editSource.portal_name);
        setFiltersDescription(editSource.filters_description || "");
      } else {
        setUrl("");
        setPortalName("");
        setFiltersDescription("");
      }
      setErrors({});
    }
  }, [open, editSource]);

  function validate(): boolean {
    const newErrors: Record<string, string> = {};
    const trimmedUrl = url.trim();
    const trimmedName = portalName.trim();

    if (!trimmedUrl) {
      newErrors.url = "URL is required.";
    } else {
      try {
        const parsed = new URL(trimmedUrl);
        if (!["http:", "https:"].includes(parsed.protocol)) {
          newErrors.url = "URL must start with http:// or https://";
        }
      } catch {
        newErrors.url = "Please enter a valid URL.";
      }
    }

    if (!trimmedName) {
      newErrors.portal_name = "Portal name is required.";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }

  async function handleSubmit() {
    if (!validate()) return;

    setSaving(true);
    try {
      if (isEdit && editSource) {
        await updateSource(editSource.id, {
          url: url.trim(),
          portal_name: portalName.trim(),
          filters_description: filtersDescription.trim(),
        });
        showToast("Source updated successfully.", "success");
      } else {
        const payload: JobSourceCreate = {
          url: url.trim(),
          portal_name: portalName.trim(),
          filters_description: filtersDescription.trim() || undefined,
        };
        await createSource(payload);
        showToast("Source added successfully.", "success");
      }
      onSaved();
      onClose();
    } catch (err: unknown) {
      const errorDetail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail || "Failed to save source.";
      if (errorDetail.includes("already being monitored")) {
        setErrors({ url: errorDetail });
      } else {
        showToast(errorDetail, "error");
      }
    } finally {
      setSaving(false);
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={isEdit ? "Edit Source" : "Add Source"}>
      <div className="space-y-4">
        <Input
          label="URL"
          placeholder="https://company.com/careers"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          error={errors.url}
        />
        <Input
          label="Portal Name"
          placeholder="e.g., Google Careers, Stripe Jobs"
          value={portalName}
          onChange={(e) => setPortalName(e.target.value)}
          error={errors.portal_name}
        />
        <div className="w-full">
          <label className="block text-sm font-medium text-text mb-1.5">
            Filters / Description (optional)
          </label>
          <textarea
            className="w-full h-20 px-3 py-2 rounded-lg border border-border bg-bg text-text placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-1 resize-none"
            placeholder="e.g., Remote only, Senior Engineer roles"
            value={filtersDescription}
            onChange={(e) => setFiltersDescription(e.target.value)}
          />
        </div>
        <div className="flex justify-end gap-3 pt-2">
          <Button variant="secondary" onClick={onClose} disabled={saving}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} loading={saving}>
            {isEdit ? "Save Changes" : "Add Source"}
          </Button>
        </div>
      </div>
    </Modal>
  );
}

// ---------------------------------------------------------------------------
// Delete Confirmation Modal
// ---------------------------------------------------------------------------

interface DeleteConfirmProps {
  open: boolean;
  onClose: () => void;
  onConfirm: () => void;
  source: JobSource | null;
  deleting: boolean;
}

function DeleteConfirmModal({
  open,
  onClose,
  onConfirm,
  source,
  deleting,
}: DeleteConfirmProps) {
  if (!source) return null;

  return (
    <Modal open={open} onClose={onClose} title="Delete Source">
      <div className="space-y-4">
        <p className="text-sm text-text">
          Are you sure you want to delete{" "}
          <span className="font-semibold">{source.portal_name}</span>?
        </p>
        {source.jobs_found > 0 && (
          <div className="flex items-start gap-2 rounded-lg bg-warning/10 border border-warning/30 p-3">
            <AlertCircle className="size-4 text-warning mt-0.5 shrink-0" />
            <p className="text-sm text-warning">
              This source has {source.jobs_found} associated job
              {source.jobs_found > 1 ? "s" : ""}. The jobs will remain in the database.
            </p>
          </div>
        )}
        <div className="flex justify-end gap-3 pt-2">
          <Button variant="secondary" onClick={onClose} disabled={deleting}>
            Cancel
          </Button>
          <Button variant="danger" onClick={onConfirm} loading={deleting}>
            Delete Source
          </Button>
        </div>
      </div>
    </Modal>
  );
}

// ---------------------------------------------------------------------------
// Sources Page
// ---------------------------------------------------------------------------

export default function Sources() {
  const [sources, setSources] = useState<JobSource[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modal state
  const [formOpen, setFormOpen] = useState(false);
  const [editingSource, setEditingSource] = useState<JobSource | null>(null);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [deletingSource, setDeletingSource] = useState<JobSource | null>(null);
  const [deleting, setDeleting] = useState(false);

  // Scanning state
  const [scanningId, setScanningId] = useState<number | null>(null);

  const loadSources = useCallback(async () => {
    try {
      setError(null);
      const data = await getSources();
      setSources(data);
    } catch {
      setError("Failed to load sources.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadSources();
  }, [loadSources]);

  function handleAddClick() {
    setEditingSource(null);
    setFormOpen(true);
  }

  function handleEditClick(source: JobSource) {
    setEditingSource(source);
    setFormOpen(true);
  }

  function handleDeleteClick(source: JobSource) {
    setDeletingSource(source);
    setDeleteOpen(true);
  }

  async function handleDeleteConfirm() {
    if (!deletingSource) return;
    setDeleting(true);
    try {
      await deleteSource(deletingSource.id);
      showToast("Source deleted.", "success");
      setDeleteOpen(false);
      setDeletingSource(null);
      loadSources();
    } catch {
      showToast("Failed to delete source.", "error");
    } finally {
      setDeleting(false);
    }
  }

  async function handleToggleActive(source: JobSource) {
    try {
      await updateSource(source.id, { is_active: !source.is_active });
      showToast(
        source.is_active ? "Source paused." : "Source resumed.",
        "success"
      );
      loadSources();
    } catch {
      showToast("Failed to update source.", "error");
    }
  }

  async function handleScan(source: JobSource) {
    setScanningId(source.id);
    try {
      const result = await scanSource(source.id);
      showToast(result.message, "success");
      loadSources();
    } catch (err: unknown) {
      const errorDetail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail || "Scan failed.";
      showToast(errorDetail, "error");
    } finally {
      setScanningId(null);
    }
  }

  function formatDate(dateStr: string | null): string {
    if (!dateStr) return "Never";
    try {
      return new Date(dateStr).toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return dateStr;
    }
  }

  // Loading skeleton
  if (loading) {
    return (
      <div>
        <div className="flex items-center justify-between mb-6">
          <Skeleton width={180} height={32} />
          <Skeleton width={120} height={36} />
        </div>
        <Card>
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} height={48} className="w-full rounded-md" />
            ))}
          </div>
        </Card>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div>
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-text">Job Sources</h1>
        </div>
        <Card>
          <div className="flex flex-col items-center py-12 text-center">
            <AlertCircle className="size-10 text-danger mb-3" />
            <p className="text-sm text-danger mb-4">{error}</p>
            <Button variant="secondary" onClick={loadSources}>
              Retry
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  // Empty state
  if (sources.length === 0) {
    return (
      <div>
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-text">Job Sources</h1>
        </div>

        <Card>
          <div className="flex flex-col items-center py-16 text-center">
            <Globe className="size-12 text-border mb-4" />
            <h2 className="text-base font-semibold text-text mb-1">
              No sources yet
            </h2>
            <p className="text-sm text-text-muted mb-6 max-w-sm">
              Add career page URLs to start monitoring for new job listings.
              The scraper will check these pages for you.
            </p>
            <Button onClick={handleAddClick}>
              <Plus className="size-4" />
              Add Source
            </Button>
          </div>
        </Card>

        <SourceFormModal
          open={formOpen}
          onClose={() => setFormOpen(false)}
          onSaved={loadSources}
          editSource={null}
        />
      </div>
    );
  }

  // Sources table
  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-text">Job Sources</h1>
        <Button onClick={handleAddClick}>
          <Plus className="size-4" />
          Add Source
        </Button>
      </div>

      <Card className="p-0 overflow-hidden">
        <Table>
          <TableHeader>
            <TableCell header>Name</TableCell>
            <TableCell header>URL</TableCell>
            <TableCell header>Status</TableCell>
            <TableCell header>Last Checked</TableCell>
            <TableCell header>Jobs</TableCell>
            <TableCell header className="text-right">
              Actions
            </TableCell>
          </TableHeader>
          <tbody>
            {sources.map((source) => (
              <TableRow key={source.id}>
                <TableCell>
                  <span className="font-medium">{source.portal_name}</span>
                  {source.filters_description && (
                    <span className="block text-xs text-text-muted mt-0.5">
                      {source.filters_description}
                    </span>
                  )}
                </TableCell>
                <TableCell>
                  <a
                    href={source.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary hover:text-primary-hover inline-flex items-center gap-1 max-w-[240px] truncate"
                    title={source.url}
                  >
                    <span className="truncate">{source.url}</span>
                    <ExternalLink className="size-3 shrink-0" />
                  </a>
                </TableCell>
                <TableCell>
                  <Badge variant={source.is_active ? "success" : "default"}>
                    {source.is_active ? "Active" : "Paused"}
                  </Badge>
                </TableCell>
                <TableCell>
                  <span className="text-text-muted text-xs">
                    {formatDate(source.last_checked)}
                  </span>
                </TableCell>
                <TableCell>
                  <span className="font-medium">{source.jobs_found}</span>
                </TableCell>
                <TableCell>
                  <div className="flex items-center justify-end gap-1">
                    <button
                      type="button"
                      onClick={() => handleScan(source)}
                      disabled={!source.is_active || scanningId === source.id}
                      className="p-1.5 rounded-md text-text-muted hover:text-primary hover:bg-primary/5 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                      title="Scan Now"
                    >
                      {scanningId === source.id ? (
                        <RefreshCw className="size-4 animate-spin" />
                      ) : (
                        <Search className="size-4" />
                      )}
                    </button>
                    <button
                      type="button"
                      onClick={() => handleToggleActive(source)}
                      className="p-1.5 rounded-md text-text-muted hover:text-warning hover:bg-warning/5 transition-colors"
                      title={source.is_active ? "Pause" : "Resume"}
                    >
                      {source.is_active ? (
                        <Pause className="size-4" />
                      ) : (
                        <Play className="size-4" />
                      )}
                    </button>
                    <button
                      type="button"
                      onClick={() => handleEditClick(source)}
                      className="p-1.5 rounded-md text-text-muted hover:text-text hover:bg-surface transition-colors"
                      title="Edit"
                    >
                      <Pencil className="size-4" />
                    </button>
                    <button
                      type="button"
                      onClick={() => handleDeleteClick(source)}
                      className="p-1.5 rounded-md text-text-muted hover:text-danger hover:bg-danger/5 transition-colors"
                      title="Delete"
                    >
                      <Trash2 className="size-4" />
                    </button>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </tbody>
        </Table>
      </Card>

      <SourceFormModal
        open={formOpen}
        onClose={() => setFormOpen(false)}
        onSaved={loadSources}
        editSource={editingSource}
      />

      <DeleteConfirmModal
        open={deleteOpen}
        onClose={() => {
          setDeleteOpen(false);
          setDeletingSource(null);
        }}
        onConfirm={handleDeleteConfirm}
        source={deletingSource}
        deleting={deleting}
      />
    </div>
  );
}
