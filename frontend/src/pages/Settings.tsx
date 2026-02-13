import { useState, useEffect } from 'react';
import { Mail, Key, Clock, Save, Send } from 'lucide-react';
import { Card, Button, Input, showToast } from '../components/ui';
import { getSettings, updateSettings, sendTestEmail } from '../api';

interface Settings {
  id: number;
  notification_email: string | null;
  smtp_host: string | null;
  smtp_port: number | null;
  smtp_user: string | null;
  smtp_password_set: boolean;
  openai_api_key_set: boolean;
  openai_model: string | null;
  scan_frequency: number | null;
  scan_window_start: string | null;
  scan_window_end: string | null;
}

export default function SettingsPage() {
  const [settings, setSettings] = useState<Settings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testingEmail, setTestingEmail] = useState(false);

  // Form state
  const [notificationEmail, setNotificationEmail] = useState('');
  const [smtpHost, setSmtpHost] = useState('smtp.gmail.com');
  const [smtpPort, setSmtpPort] = useState(587);
  const [smtpUser, setSmtpUser] = useState('');
  const [smtpPassword, setSmtpPassword] = useState('');
  const [openaiApiKey, setOpenaiApiKey] = useState('');
  const [openaiModel, setOpenaiModel] = useState('gpt-4o-mini');
  const [scanFrequency, setScanFrequency] = useState(5);
  const [scanWindowStart, setScanWindowStart] = useState('');
  const [scanWindowEnd, setScanWindowEnd] = useState('');

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const data = await getSettings();
      setSettings(data);
      
      // Populate form
      setNotificationEmail(data.notification_email || '');
      setSmtpHost(data.smtp_host || 'smtp.gmail.com');
      setSmtpPort(data.smtp_port || 587);
      setSmtpUser(data.smtp_user || '');
      setOpenaiModel(data.openai_model || 'gpt-4o-mini');
      setScanFrequency(data.scan_frequency || 5);
      setScanWindowStart(data.scan_window_start || '');
      setScanWindowEnd(data.scan_window_end || '');
      
      setLoading(false);
    } catch (error) {
      console.error('Failed to load settings:', error);
      showToast({ message: 'Failed to load settings', variant: 'error' });
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const updateData: any = {
        notification_email: notificationEmail || null,
        smtp_host: smtpHost,
        smtp_port: smtpPort,
        smtp_user: smtpUser || null,
        openai_model: openaiModel,
        scan_frequency: scanFrequency,
        scan_window_start: scanWindowStart || null,
        scan_window_end: scanWindowEnd || null,
      };

      // Only include password if it was changed
      if (smtpPassword) {
        updateData.smtp_password = smtpPassword;
      }

      // Only include API key if it was changed
      if (openaiApiKey) {
        updateData.openai_api_key = openaiApiKey;
      }

      const updatedSettings = await updateSettings(updateData);
      setSettings(updatedSettings);
      
      // Clear sensitive fields after save
      setSmtpPassword('');
      setOpenaiApiKey('');
      
      showToast({ message: 'Settings saved successfully', variant: 'success' });
    } catch (error: any) {
      console.error('Failed to save settings:', error);
      const message = error.response?.data?.detail || 'Failed to save settings';
      showToast({ message, variant: 'error' });
    } finally {
      setSaving(false);
    }
  };

  const handleTestEmail = async () => {
    if (!notificationEmail) {
      showToast({ message: 'Please enter a notification email first', variant: 'error' });
      return;
    }

    setTestingEmail(true);
    try {
      await sendTestEmail(notificationEmail);
      showToast({ message: `Test email sent to ${notificationEmail}`, variant: 'success' });
    } catch (error: any) {
      console.error('Failed to send test email:', error);
      const message = error.response?.data?.detail || 'Failed to send test email';
      showToast({ message, variant: 'error' });
    } finally {
      setTestingEmail(false);
    }
  };

  if (loading) {
    return (
      <div>
        <h1 className="text-2xl font-bold text-text mb-6">Settings</h1>
        <div className="space-y-6">
          <Card>
            <div className="h-48 animate-pulse bg-surface"></div>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-text">Settings</h1>
        <Button onClick={handleSave} disabled={saving}>
          <Save className="size-4 mr-2" />
          {saving ? 'Saving...' : 'Save Settings'}
        </Button>
      </div>

      <div className="space-y-6">
        {/* Email Settings */}
        <Card>
          <div className="flex items-center mb-4">
            <Mail className="size-5 mr-2 text-primary" />
            <h2 className="text-lg font-semibold text-text">Email Configuration</h2>
          </div>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-text mb-1">
                Notification Email
              </label>
              <Input
                type="email"
                value={notificationEmail}
                onChange={(e) => setNotificationEmail(e.target.value)}
                placeholder="your.email@example.com"
              />
              <p className="text-xs text-text-muted mt-1">
                Where you'll receive job notifications
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-text mb-1">
                  SMTP Host
                </label>
                <Input
                  value={smtpHost}
                  onChange={(e) => setSmtpHost(e.target.value)}
                  placeholder="smtp.gmail.com"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-text mb-1">
                  SMTP Port
                </label>
                <Input
                  type="number"
                  value={smtpPort}
                  onChange={(e) => setSmtpPort(parseInt(e.target.value))}
                  placeholder="587"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-text mb-1">
                SMTP Username
              </label>
              <Input
                value={smtpUser}
                onChange={(e) => setSmtpUser(e.target.value)}
                placeholder="your.email@gmail.com"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-text mb-1">
                SMTP Password {settings?.smtp_password_set && '(configured)'}
              </label>
              <Input
                type="password"
                value={smtpPassword}
                onChange={(e) => setSmtpPassword(e.target.value)}
                placeholder={settings?.smtp_password_set ? '••••••••' : 'Enter password'}
              />
              <p className="text-xs text-text-muted mt-1">
                For Gmail, use an App Password. Leave blank to keep existing password.
              </p>
            </div>

            <Button
              variant="secondary"
              onClick={handleTestEmail}
              disabled={testingEmail || !notificationEmail}
            >
              <Send className="size-4 mr-2" />
              {testingEmail ? 'Sending...' : 'Send Test Email'}
            </Button>
          </div>
        </Card>

        {/* OpenAI Settings */}
        <Card>
          <div className="flex items-center mb-4">
            <Key className="size-5 mr-2 text-primary" />
            <h2 className="text-lg font-semibold text-text">OpenAI Configuration</h2>
          </div>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-text mb-1">
                API Key {settings?.openai_api_key_set && '(configured)'}
              </label>
              <Input
                type="password"
                value={openaiApiKey}
                onChange={(e) => setOpenaiApiKey(e.target.value)}
                placeholder={settings?.openai_api_key_set ? '••••••••••••••••••••••••••••••••' : 'sk-...'}
              />
              <p className="text-xs text-text-muted mt-1">
                Leave blank to keep existing key. Get your key from{' '}
                <a href="https://platform.openai.com/api-keys" target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">
                  OpenAI
                </a>
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-text mb-1">
                Model
              </label>
              <select
                value={openaiModel}
                onChange={(e) => setOpenaiModel(e.target.value)}
                className="w-full px-3 py-2 border border-border rounded-lg bg-bg text-text focus:outline-none focus:ring-2 focus:ring-primary"
              >
                <option value="gpt-4o-mini">GPT-4o Mini (Recommended)</option>
                <option value="gpt-4o">GPT-4o</option>
                <option value="gpt-4-turbo">GPT-4 Turbo</option>
                <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
              </select>
            </div>
          </div>
        </Card>

        {/* Scan Preferences */}
        <Card>
          <div className="flex items-center mb-4">
            <Clock className="size-5 mr-2 text-primary" />
            <h2 className="text-lg font-semibold text-text">Scan Preferences</h2>
          </div>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-text mb-1">
                Scan Frequency (per day)
              </label>
              <select
                value={scanFrequency}
                onChange={(e) => setScanFrequency(parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-border rounded-lg bg-bg text-text focus:outline-none focus:ring-2 focus:ring-primary"
              >
                <option value={3}>3 times per day</option>
                <option value={5}>5 times per day (Recommended)</option>
                <option value={8}>8 times per day</option>
                <option value={12}>12 times per day</option>
              </select>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-text mb-1">
                  Scan Window Start (optional)
                </label>
                <Input
                  type="time"
                  value={scanWindowStart}
                  onChange={(e) => setScanWindowStart(e.target.value)}
                  placeholder="09:00"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-text mb-1">
                  Scan Window End (optional)
                </label>
                <Input
                  type="time"
                  value={scanWindowEnd}
                  onChange={(e) => setScanWindowEnd(e.target.value)}
                  placeholder="18:00"
                />
              </div>
            </div>
            <p className="text-xs text-text-muted">
              Leave blank to scan 24/7. Set a time window to only scan during specific hours.
            </p>
          </div>
        </Card>
      </div>

    </div>
  );
}
