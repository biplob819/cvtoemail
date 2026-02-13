import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { FileText, Globe, Briefcase, Clock, Upload, AlertCircle } from 'lucide-react';
import { Card, Badge, Skeleton, Button } from '../components/ui';
import { getCV, getDashboardStats, getRecentJobs, getSystemStatus } from '../api';

interface DashboardStats {
  active_sources: number;
  new_jobs_24h: number;
  cvs_sent_7d: number;
  last_scan: string | null;
  total_jobs: number;
  total_applications: number;
}

interface RecentJob {
  id: number;
  title: string;
  company: string;
  location: string | null;
  status: string;
  discovered_at: string;
  source_name: string;
}

interface SystemStatus {
  celery_running: boolean;
  next_scan: string | null;
}

export default function Dashboard() {
  const [hasCV, setHasCV] = useState<boolean | null>(null);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recentJobs, setRecentJobs] = useState<RecentJob[]>([]);
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      // Load CV status
      const cv = await getCV();
      setHasCV(cv !== null && cv.id !== undefined);

      // If CV exists, load dashboard data
      if (cv && cv.id) {
        const [statsData, jobsData, statusData] = await Promise.all([
          getDashboardStats(),
          getRecentJobs(),
          getSystemStatus(),
        ]);
        setStats(statsData);
        setRecentJobs(jobsData);
        setSystemStatus(statusData);
      }
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
      setHasCV(false);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'Never';
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    if (days < 7) return `${days}d ago`;
    return date.toLocaleDateString();
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      'New': 'bg-success/10 text-success',
      'Viewed': 'bg-primary/10 text-primary',
      'CV Generated': 'bg-warning/10 text-warning',
      'CV Sent': 'bg-primary/10 text-primary',
      'Skipped': 'bg-text-muted/10 text-text-muted',
    };
    return colors[status] || 'bg-surface text-text-muted';
  };

  if (loading) {
    return (
      <div>
        <Skeleton height={32} width={200} className="mb-6" />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} height={100} className="rounded-lg" />
          ))}
        </div>
        <Skeleton height={300} className="rounded-lg" />
      </div>
    );
  }

  // First-launch onboarding state
  if (!hasCV) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mb-6">
          <Briefcase className="size-8 text-primary" />
        </div>
        <h1 className="text-2xl font-bold text-text mb-2">Welcome to Auto Job Apply</h1>
        <p className="text-text-muted max-w-md mb-8">
          Get started by uploading your CV. The app will help you monitor job boards and generate
          tailored ATS-friendly resumes for each opportunity.
        </p>

        <div className="flex flex-col sm:flex-row gap-3">
          <Link to="/cv">
            <Button variant="primary" className="gap-2">
              <Upload className="size-4" />
              Upload Your CV
            </Button>
          </Link>
          <Link to="/sources">
            <Button variant="secondary" className="gap-2">
              <Globe className="size-4" />
              Add Job Source
            </Button>
          </Link>
        </div>

        {/* Setup steps */}
        <div className="mt-12 w-full max-w-lg text-left">
          <h2 className="text-sm font-semibold text-text-muted uppercase tracking-wider mb-4">
            Setup Steps
          </h2>
          <div className="space-y-3">
            {[
              { step: 1, label: 'Upload your CV', desc: 'PDF or DOCX, max 5MB', link: '/cv', done: false },
              { step: 2, label: 'Add job sources', desc: 'Paste career page URLs to monitor', link: '/sources', done: false },
              { step: 3, label: 'Configure settings', desc: 'Set up email and OpenAI API key', link: '/settings', done: false },
            ].map((item) => (
              <Link key={item.step} to={item.link}>
                <Card className="flex items-center gap-4 hover:border-primary/30 transition-colors cursor-pointer !p-4">
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold shrink-0
                      ${item.done ? 'bg-success/10 text-success' : 'bg-surface text-text-muted border border-border'}`}
                  >
                    {item.step}
                  </div>
                  <div>
                    <div className="text-sm font-medium text-text">{item.label}</div>
                    <div className="text-xs text-text-muted">{item.desc}</div>
                  </div>
                </Card>
              </Link>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // Regular dashboard
  return (
    <div>
      <h1 className="text-2xl font-bold text-text mb-6">Dashboard</h1>

      {/* Celery warning banner */}
      {systemStatus && !systemStatus.celery_running && (
        <div className="mb-6 p-4 bg-warning/10 border border-warning/30 rounded-lg flex items-start gap-3">
          <AlertCircle className="size-5 text-warning shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-text">Celery Worker Not Running</p>
            <p className="text-xs text-text-muted mt-1">
              The background job monitoring service is not active. Start Celery to enable automatic job discovery.
            </p>
          </div>
        </div>
      )}

      {/* Stats bar */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <Card className="flex items-center gap-4 !p-4">
          <div className="text-primary">
            <Globe className="size-5" />
          </div>
          <div>
            <div className="text-2xl font-bold text-text">{stats?.active_sources ?? 0}</div>
            <div className="text-xs text-text-muted">Active Sources</div>
          </div>
        </Card>

        <Card className="flex items-center gap-4 !p-4">
          <div className="text-success">
            <Briefcase className="size-5" />
          </div>
          <div>
            <div className="text-2xl font-bold text-text">{stats?.new_jobs_24h ?? 0}</div>
            <div className="text-xs text-text-muted">New Jobs (24h)</div>
          </div>
        </Card>

        <Card className="flex items-center gap-4 !p-4">
          <div className="text-warning">
            <FileText className="size-5" />
          </div>
          <div>
            <div className="text-2xl font-bold text-text">{stats?.cvs_sent_7d ?? 0}</div>
            <div className="text-xs text-text-muted">CVs Sent (7d)</div>
          </div>
        </Card>

        <Card className="flex items-center gap-4 !p-4">
          <div className="text-text-muted">
            <Clock className="size-5" />
          </div>
          <div>
            <div className="text-2xl font-bold text-text">{formatDate(stats?.last_scan ?? null)}</div>
            <div className="text-xs text-text-muted">Last Scan</div>
          </div>
        </Card>
      </div>

      {/* Recent jobs */}
      <Card>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-base font-semibold text-text">Recent Jobs</h2>
          <Link to="/jobs">
            <span className="text-sm text-primary hover:text-primary-hover font-medium">View all</span>
          </Link>
        </div>

        {recentJobs.length === 0 ? (
          <div className="flex flex-col items-center py-12 text-center">
            <Briefcase className="size-10 text-border mb-3" />
            <p className="text-sm text-text-muted mb-4">No jobs discovered yet</p>
            <Link to="/sources">
              <Button variant="secondary" className="text-sm">Add Job Source</Button>
            </Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="border-b border-border">
                <tr className="text-left">
                  <th className="pb-3 text-xs font-medium text-text-muted">Job Title</th>
                  <th className="pb-3 text-xs font-medium text-text-muted">Company</th>
                  <th className="pb-3 text-xs font-medium text-text-muted">Source</th>
                  <th className="pb-3 text-xs font-medium text-text-muted">Status</th>
                  <th className="pb-3 text-xs font-medium text-text-muted">Discovered</th>
                </tr>
              </thead>
              <tbody>
                {recentJobs.map((job) => (
                  <tr key={job.id} className="border-b border-border last:border-0">
                    <td className="py-3">
                      <Link to={`/jobs`} className="text-sm font-medium text-text hover:text-primary">
                        {job.title}
                      </Link>
                    </td>
                    <td className="py-3 text-sm text-text-muted">{job.company}</td>
                    <td className="py-3 text-sm text-text-muted">{job.source_name}</td>
                    <td className="py-3">
                      <Badge className={getStatusColor(job.status)}>{job.status}</Badge>
                    </td>
                    <td className="py-3 text-sm text-text-muted">{formatDate(job.discovered_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* System status */}
      <div className="mt-4 flex items-center gap-2 text-xs text-text-muted">
        <div className={`w-2 h-2 rounded-full ${systemStatus?.celery_running ? 'bg-success' : 'bg-text-muted'}`} />
        <span>
          Celery worker: {systemStatus?.celery_running ? 'Running' : 'Not running'}
          {systemStatus?.next_scan && ` · Next scan: ${formatDate(systemStatus.next_scan)}`}
        </span>
      </div>
    </div>
  );
}
