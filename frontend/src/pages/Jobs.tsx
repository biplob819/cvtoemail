import { useState, useEffect, useCallback } from "react";
import {
  Briefcase,
  Filter,
  ExternalLink,
  FileDown,
  SkipForward,
  CheckSquare,
  Square,
  Calendar,
  Building2,
  MapPin,
  ChevronDown,
  ChevronUp,
  AlertCircle,
} from "lucide-react";
import {
  Card,
  Button,
  Badge,
  Table,
  TableHeader,
  TableRow,
  TableCell,
  Skeleton,
  showToast,
} from "../components/ui";
import {
  getJobs,
  getSources,
  updateJob,
  bulkSkipJobs,
  generateCV,
  downloadCV,
} from "../api";
import type { Job, JobSource } from "../types";

// ---------------------------------------------------------------------------
// Main Jobs Page
// ---------------------------------------------------------------------------

export default function Jobs() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [sources, setSources] = useState<JobSource[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedJobs, setSelectedJobs] = useState<Set<number>>(new Set());
  const [expandedJobId, setExpandedJobId] = useState<number | null>(null);
  
  // Filters
  const [filterSourceId, setFilterSourceId] = useState<number | undefined>();
  const [filterStatus, setFilterStatus] = useState<string | undefined>();
  const [showFilters, setShowFilters] = useState(false);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [jobsData, sourcesData] = await Promise.all([
        getJobs({ source_id: filterSourceId, status: filterStatus }),
        getSources(),
      ]);
      setJobs(jobsData);
      setSources(sourcesData);
    } catch (err) {
      console.error("Failed to load jobs:", err);
      showToast("Failed to load jobs", "error");
    } finally {
      setLoading(false);
    }
  }, [filterSourceId, filterStatus]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // ---------------------------------------------------------------------------
  // Selection Handlers
  // ---------------------------------------------------------------------------

  function toggleSelectAll() {
    if (selectedJobs.size === jobs.length) {
      setSelectedJobs(new Set());
    } else {
      setSelectedJobs(new Set(jobs.map((j) => j.id)));
    }
  }

  function toggleSelectJob(jobId: number) {
    const newSelection = new Set(selectedJobs);
    if (newSelection.has(jobId)) {
      newSelection.delete(jobId);
    } else {
      newSelection.add(jobId);
    }
    setSelectedJobs(newSelection);
  }

  // ---------------------------------------------------------------------------
  // Job Actions
  // ---------------------------------------------------------------------------

  async function handleJobClick(jobId: number) {
    // Toggle expansion
    if (expandedJobId === jobId) {
      setExpandedJobId(null);
    } else {
      setExpandedJobId(jobId);
      
      // Mark as viewed if it's new
      const job = jobs.find((j) => j.id === jobId);
      if (job && job.is_new) {
        try {
          await updateJob(jobId, { status: "Viewed", is_new: false });
          // Update local state
          setJobs((prev) =>
            prev.map((j) =>
              j.id === jobId ? { ...j, status: "Viewed", is_new: false } : j
            )
          );
        } catch (err) {
          console.error("Failed to mark job as viewed:", err);
        }
      }
    }
  }

  async function handleSkipJob(jobId: number) {
    try {
      await updateJob(jobId, { status: "Skipped", is_new: false });
      showToast("Job skipped", "success");
      setJobs((prev) =>
        prev.map((j) =>
          j.id === jobId ? { ...j, status: "Skipped", is_new: false } : j
        )
      );
    } catch (err) {
      showToast("Failed to skip job", "error");
    }
  }

  async function handleBulkSkip() {
    if (selectedJobs.size === 0) {
      showToast("No jobs selected", "error");
      return;
    }

    try {
      const result = await bulkSkipJobs(Array.from(selectedJobs));
      showToast(`Skipped ${result.updated_count} job(s)`, "success");
      setSelectedJobs(new Set());
      await loadData();
    } catch (err) {
      showToast("Failed to skip jobs", "error");
    }
  }

  async function handleGenerateCV(jobId: number) {
    try {
      showToast("Generating CV... This may take a few moments.", "success");
      const result = await generateCV(jobId);
      showToast(result.message, "success");
      // Reload jobs to get updated status
      await loadData();
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || "Failed to generate CV";
      showToast(errorMsg, "error");
    }
  }

  function handleDownloadCV(jobId: number) {
    const downloadUrl = downloadCV(jobId);
    window.open(downloadUrl, "_blank");
  }

  // ---------------------------------------------------------------------------
  // Filter Handlers
  // ---------------------------------------------------------------------------

  function handleApplyFilters() {
    loadData();
  }

  function handleClearFilters() {
    setFilterSourceId(undefined);
    setFilterStatus(undefined);
    // Force reload
    setTimeout(() => loadData(), 0);
  }

  // ---------------------------------------------------------------------------
  // Status Badge Component
  // ---------------------------------------------------------------------------

  function getStatusBadge(status: string) {
    const variants: Record<string, "default" | "success" | "warning" | "danger"> = {
      New: "default",
      Viewed: "warning",
      "CV Generated": "success",
      "CV Sent": "success",
      Skipped: "danger",
    };
    return <Badge variant={variants[status] || "default"}>{status}</Badge>;
  }

  // ---------------------------------------------------------------------------
  // Empty State
  // ---------------------------------------------------------------------------

  if (!loading && jobs.length === 0 && !filterSourceId && !filterStatus) {
    return (
      <div>
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-text">Jobs</h1>
        </div>

        <Card>
          <div className="flex flex-col items-center py-16 text-center">
            <Briefcase className="size-12 text-border mb-4" />
            <h2 className="text-base font-semibold text-text mb-1">No jobs discovered yet</h2>
            <p className="text-sm text-text-muted mb-6 max-w-sm">
              Jobs will appear here automatically when the scheduled monitoring runs.
              You can also trigger a manual scan from the Sources page.
            </p>
            <Button variant="secondary" onClick={() => window.location.href = "/sources"}>
              Go to Sources
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  // ---------------------------------------------------------------------------
  // Main UI
  // ---------------------------------------------------------------------------

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-text">Jobs</h1>
        <div className="flex items-center gap-3">
          {selectedJobs.size > 0 && (
            <Button variant="danger" onClick={handleBulkSkip}>
              <SkipForward className="size-4" />
              Skip Selected ({selectedJobs.size})
            </Button>
          )}
          <Button
            variant="secondary"
            onClick={() => setShowFilters(!showFilters)}
          >
            <Filter className="size-4" />
            {showFilters ? "Hide Filters" : "Show Filters"}
          </Button>
        </div>
      </div>

      {/* Filter Bar */}
      {showFilters && (
        <Card className="mb-4 p-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label htmlFor="filter-source" className="block text-sm font-medium text-text mb-1.5">
                Source
              </label>
              <select
                id="filter-source"
                className="w-full h-10 px-3 rounded-lg border border-border bg-bg text-text focus:outline-none focus:ring-2 focus:ring-primary"
                value={filterSourceId || ""}
                onChange={(e) =>
                  setFilterSourceId(e.target.value ? Number(e.target.value) : undefined)
                }
              >
                <option value="">All Sources</option>
                {sources.map((source) => (
                  <option key={source.id} value={source.id}>
                    {source.portal_name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label htmlFor="filter-status" className="block text-sm font-medium text-text mb-1.5">
                Status
              </label>
              <select
                id="filter-status"
                className="w-full h-10 px-3 rounded-lg border border-border bg-bg text-text focus:outline-none focus:ring-2 focus:ring-primary"
                value={filterStatus || ""}
                onChange={(e) => setFilterStatus(e.target.value || undefined)}
              >
                <option value="">All Status</option>
                <option value="New">New</option>
                <option value="Viewed">Viewed</option>
                <option value="CV Generated">CV Generated</option>
                <option value="CV Sent">CV Sent</option>
                <option value="Skipped">Skipped</option>
              </select>
            </div>

            <div className="flex items-end gap-2">
              <Button variant="primary" onClick={handleApplyFilters}>
                Apply Filters
              </Button>
              <Button variant="secondary" onClick={handleClearFilters}>
                Clear
              </Button>
            </div>
          </div>
        </Card>
      )}

      {/* Jobs Table */}
      <Card>
        {loading ? (
          <div className="space-y-3">
            <Skeleton className="h-12" />
            <Skeleton className="h-16" />
            <Skeleton className="h-16" />
            <Skeleton className="h-16" />
          </div>
        ) : jobs.length === 0 ? (
          <div className="flex flex-col items-center py-12 text-center">
            <AlertCircle className="size-10 text-text-muted mb-3" />
            <p className="text-sm text-text-muted">
              No jobs found matching the selected filters.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <Table>
              <thead>
                <TableHeader>
                  <th className="w-12 px-4">
                    <button
                      onClick={toggleSelectAll}
                      className="text-text-muted hover:text-text"
                      aria-label="Select all"
                    >
                      {selectedJobs.size === jobs.length ? (
                        <CheckSquare className="size-5" />
                      ) : (
                        <Square className="size-5" />
                      )}
                    </button>
                  </th>
                  <th className="text-left px-4 py-3">Job Title</th>
                  <th className="text-left px-4 py-3">Company</th>
                  <th className="text-left px-4 py-3">Location</th>
                  <th className="text-left px-4 py-3">Source</th>
                  <th className="text-left px-4 py-3">Date</th>
                  <th className="text-left px-4 py-3">Status</th>
                  <th className="text-right px-4 py-3 w-12"></th>
                </TableHeader>
              </thead>
              <tbody>
                {jobs.map((job) => (
                  <>
                    <TableRow
                      key={job.id}
                      onClick={() => handleJobClick(job.id)}
                      className="cursor-pointer hover:bg-surface"
                    >
                      <TableCell onClick={(e) => e.stopPropagation()}>
                        <button
                          onClick={() => toggleSelectJob(job.id)}
                          className="text-text-muted hover:text-text"
                          aria-label="Select job"
                        >
                          {selectedJobs.has(job.id) ? (
                            <CheckSquare className="size-5" />
                          ) : (
                            <Square className="size-5" />
                          )}
                        </button>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          {job.is_new && (
                            <span className="size-2 rounded-full bg-primary flex-shrink-0" />
                          )}
                          <span className="font-medium text-text">{job.title}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2 text-text-muted">
                          <Building2 className="size-4 flex-shrink-0" />
                          <span>{job.company || "—"}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2 text-text-muted">
                          <MapPin className="size-4 flex-shrink-0" />
                          <span>{job.location || "—"}</span>
                        </div>
                      </TableCell>
                      <TableCell className="text-text-muted">
                        {job.source_name || "Unknown"}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2 text-text-muted text-sm">
                          <Calendar className="size-4 flex-shrink-0" />
                          <span>
                            {new Date(job.discovered_at).toLocaleDateString()}
                          </span>
                        </div>
                      </TableCell>
                      <TableCell>{getStatusBadge(job.status)}</TableCell>
                      <TableCell className="text-right">
                        {expandedJobId === job.id ? (
                          <ChevronUp className="size-5 text-text-muted" />
                        ) : (
                          <ChevronDown className="size-5 text-text-muted" />
                        )}
                      </TableCell>
                    </TableRow>

                    {/* Expanded Detail Panel */}
                    {expandedJobId === job.id && (
                      <tr>
                        <td colSpan={8} className="px-4 py-4 bg-surface border-t border-border">
                          <div className="space-y-4">
                            <div>
                              <h3 className="text-sm font-semibold text-text mb-2">
                                Job Description
                              </h3>
                              <div className="text-sm text-text-muted whitespace-pre-wrap max-h-64 overflow-y-auto">
                                {job.description || (
                                  <p className="italic text-text-muted">
                                    No description available
                                  </p>
                                )}
                              </div>
                            </div>

                            <div className="flex items-center gap-3 pt-2 border-t border-border">
                              <Button
                                variant="secondary"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  window.open(job.url, "_blank");
                                }}
                              >
                                <ExternalLink className="size-4" />
                                View Job Posting
                              </Button>
                              
                              {job.cv_pdf_path ? (
                                <>
                                  <Button
                                    variant="primary"
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      handleDownloadCV(job.id);
                                    }}
                                  >
                                    <FileDown className="size-4" />
                                    Download CV
                                  </Button>
                                  <Button
                                    variant="secondary"
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      handleGenerateCV(job.id);
                                    }}
                                  >
                                    Regenerate CV
                                  </Button>
                                </>
                              ) : (
                                <Button
                                  variant="primary"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleGenerateCV(job.id);
                                  }}
                                  disabled={!job.description || job.description.length < 50}
                                >
                                  <FileDown className="size-4" />
                                  Generate CV
                                </Button>
                              )}
                              
                              {job.status !== "Skipped" && (
                                <Button
                                  variant="danger"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleSkipJob(job.id);
                                  }}
                                >
                                  <SkipForward className="size-4" />
                                  Skip
                                </Button>
                              )}
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </>
                ))}
              </tbody>
            </Table>
          </div>
        )}
      </Card>

      {/* Results Summary */}
      {!loading && jobs.length > 0 && (
        <div className="mt-4 text-sm text-text-muted text-center">
          Showing {jobs.length} job{jobs.length !== 1 ? "s" : ""}
        </div>
      )}
    </div>
  );
}
