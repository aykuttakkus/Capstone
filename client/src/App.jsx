import { useCallback, useEffect, useRef, useState } from 'react';
import axios from 'axios';
import {
  AlertTriangle,
  Archive,
  Brain,
  Camera,
  CircleHelp,
  Database,
  ExternalLink,
  FileText,
  KeyRound,
  LogIn,
  LogOut,
  Mail,
  Menu,
  MoreHorizontal,
  Send,
  Settings,
  Shield,
  SlidersHorizontal,
  Sparkles,
  User,
  UserPlus,
  Check,
  ChevronDown,
  X,
  Search,
  SquarePen,
  PanelLeft,
  Trash2,
  ChevronRight,
  LifeBuoy,
  ClipboardList,
  ShieldCheck,
  Lightbulb,
} from 'lucide-react';
import { API_URL } from './config';

const APP_NAME = 'Calma';
const TOKEN_KEY = 'calma_token';
const TOKEN_KEY_LEGACY = 'mindguide_token';
const ONBOARDING_KEY = 'calma_onboarding_v1';
const ONBOARDING_KEY_LEGACY = 'mindguide_onboarding_v1';
const ONBOARDING_COMPLETE_KEY = 'calma_onboarding_complete_v1';
const ONBOARDING_COMPLETE_KEY_LEGACY = 'mindguide_onboarding_complete_v1';
const THEME_KEY = 'calma_theme';
const THEME_KEY_LEGACY = 'mindguide_theme';
const api = axios.create({ baseURL: API_URL });

const initialAuthForm = { email: '', password: '', confirmPassword: '' };
const initialProfileDraft = {
  displayName: '',
  username: '',
  mainTriggers: '',
  supportSystem: '',
  helpfulCoping: '',
  communicationStyle: 'Warm_and_Gentle',
  responseLengthPreference: 'Balanced',
  goalsForSupport: 'Emotional_Support',
  useMoodContext: false,
  useJournalContext: false,
  useMemoryContext: true,
};
const initialMoodDraft = { mood_score: 5, energy_score: 5, anxiety_score: 5, sleep_quality: 5, notes: '' };
const initialJournalDraft = { title: '', content: '', consent_for_chat: false };

const getOnboardingStorageKey = (email = 'guest') => `${ONBOARDING_KEY}:${email.toLowerCase()}`;
const getLegacyOnboardingStorageKey = (email = 'guest') => `${ONBOARDING_KEY_LEGACY}:${email.toLowerCase()}`;
const getOnboardingCompleteKey = (email = 'guest') => `${ONBOARDING_COMPLETE_KEY}:${email.toLowerCase()}`;
const getLegacyOnboardingCompleteKey = (email = 'guest') => `${ONBOARDING_COMPLETE_KEY_LEGACY}:${email.toLowerCase()}`;

const readStorageValue = (key, legacyKeys = []) => {
  try {
    const currentValue = localStorage.getItem(key);
    if (currentValue !== null) {
      legacyKeys.forEach((legacyKey) => localStorage.removeItem(legacyKey));
      return currentValue;
    }

    for (const legacyKey of legacyKeys) {
      const legacyValue = localStorage.getItem(legacyKey);
      if (legacyValue !== null) {
        localStorage.setItem(key, legacyValue);
        localStorage.removeItem(legacyKey);
        return legacyValue;
      }
    }

    return null;
  } catch {
    return null;
  }
};

const writeStorageValue = (key, value, legacyKeys = []) => {
  try {
    localStorage.setItem(key, value);
    legacyKeys.forEach((legacyKey) => localStorage.removeItem(legacyKey));
  } catch {
    // Ignore storage failures.
  }
};

const readOnboardingState = (email) => {
  try {
    const normalizedEmail = (email ?? 'guest').toLowerCase();
    const raw = readStorageValue(getOnboardingStorageKey(normalizedEmail), [getLegacyOnboardingStorageKey(normalizedEmail)]);

    if (!raw) return null;

    const parsed = JSON.parse(raw);
    if (parsed?.completed) {
      writeStorageValue(getOnboardingCompleteKey(normalizedEmail), 'true', [getLegacyOnboardingCompleteKey(normalizedEmail)]);
    }

    return parsed;
  } catch {
    return null;
  }
};

const writeOnboardingState = (email, value) => {
  try {
    const normalizedEmail = (email ?? 'guest').toLowerCase();
    writeStorageValue(
      getOnboardingStorageKey(normalizedEmail),
      JSON.stringify(value),
      [getLegacyOnboardingStorageKey(normalizedEmail)],
    );
    if (value?.completed) {
      writeStorageValue(
        getOnboardingCompleteKey(normalizedEmail),
        'true',
        [getLegacyOnboardingCompleteKey(normalizedEmail)],
      );
    }
  } catch {
    // Ignore storage failures.
  }
};

const formatDisplayName = (user) => {
  const candidate = user?.full_name || user?.name || user?.display_name || user?.email?.split('@')[0] || 'User';

  return candidate
    .split(/[._-]+|\s+/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
};

const formatRelativeTime = (value) => {
  const timestamp = new Date(value).getTime();
  if (Number.isNaN(timestamp)) return 'recently';

  const diffMinutes = Math.floor((Date.now() - timestamp) / 60000);
  if (diffMinutes < 1) return 'just now';
  if (diffMinutes < 60) return `${diffMinutes}m ago`;

  const diffHours = Math.floor(diffMinutes / 60);
  if (diffHours < 24) return `${diffHours}h ago`;

  const diffDays = Math.floor(diffHours / 24);
  return `${diffDays}d ago`;
};

const truncateText = (value, length = 42) => {
  if (!value) return 'Session';
  return value.length > length ? `${value.slice(0, length)}...` : value;
};

const mapSessionItems = (items = []) =>
  items.map((item) => ({
    id: item.id,
    title: truncateText(item.title || item.summary || item.topic || 'Session'),
    date: formatRelativeTime(item.last_message_at || item.created_at),
    safetyMode: item.safety_mode,
    status: item.status,
    topic: item.topic,
    summary: item.summary,
  }));

const getErrorMessage = (error, fallback) =>
  error?.response?.data?.detail || error?.message || fallback;

const isUnauthorized = (error) => error?.response?.status === 401;

const getInitialTheme = () => {
  try {
    const stored = readStorageValue(THEME_KEY, [THEME_KEY_LEGACY]);
    if (stored === 'light' || stored === 'dark') return stored;
  } catch {
    // Ignore storage failures and fall back to system preference.
  }

  return window.matchMedia?.('(prefers-color-scheme: dark)')?.matches ? 'dark' : 'light';
};

function App() {
  const [theme, setTheme] = useState(getInitialTheme);
  const [config, setConfig] = useState(null);
  const [stage, setStage] = useState('welcome');
  const [intakeData, setIntakeData] = useState({});
  const [screeningData, setScreeningData] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [history, setHistory] = useState([]);
  const [archivedHistory, setArchivedHistory] = useState([]);
  const [isArchivedChatsOpen, setIsArchivedChatsOpen] = useState(false);
  const [sessionQuery, setSessionQuery] = useState('');
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [newSessionRequested, setNewSessionRequested] = useState(false);
  const [sessionPanelError, setSessionPanelError] = useState('');
  const [sessionActionBusyId, setSessionActionBusyId] = useState(null);
  const [openSessionMenuId, setOpenSessionMenuId] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isBootstrapping, setIsBootstrapping] = useState(true);
  const [user, setUser] = useState(null);
  const [authMode, setAuthMode] = useState('login');
  const [authForm, setAuthForm] = useState(initialAuthForm);
  const [authError, setAuthError] = useState('');
  const [authLoading, setAuthLoading] = useState(false);
  const [sessionError, setSessionError] = useState('');
  const [isAuthActive, setIsAuthActive] = useState(false);
  const [intakePhase, setIntakePhase] = useState(null);
  const [intakeAccumulated, setIntakeAccumulated] = useState({});
  const [screeningPhase, setScreeningPhase] = useState('intro');
  const [phqAnswers, setPhqAnswers] = useState({});
  const [gadAnswers, setGadAnswers] = useState({});
  const [screeningError, setScreeningError] = useState('');
  const [onboardingAccepted, setOnboardingAccepted] = useState(false);
  const [welcomeConsent, setWelcomeConsent] = useState(false);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const [profileView, setProfileView] = useState('profile');
  const [settingsSection, setSettingsSection] = useState('general');
  const [isThemeDropdownOpen, setIsThemeDropdownOpen] = useState(false);
  const [profileNotice, setProfileNotice] = useState('');
  const [profileDraft, setProfileDraft] = useState(initialProfileDraft);
  const [profileState, setProfileState] = useState(null);
  const [moodDraft, setMoodDraft] = useState(initialMoodDraft);
  const [journalDraft, setJournalDraft] = useState(initialJournalDraft);
  const [moodTrend, setMoodTrend] = useState(null);
  const [journalInsights, setJournalInsights] = useState(null);
  const [securityMode, setSecurityMode] = useState('overview');
  const [passwordDraft, setPasswordDraft] = useState({ current: '', next: '', confirm: '' });
  const [menuPosition, setMenuPosition] = useState({ top: 0, left: 0 });

  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);
  const profilePanelRef = useRef(null);
  const userMenuRef = useRef(null);
  const sidebarRef = useRef(null);
  const sessionMenuRef = useRef(null);
  const activeSessionIdRef = useRef(null);

  useEffect(() => {
    activeSessionIdRef.current = activeSessionId;
  }, [activeSessionId]);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    document.body.dataset.theme = theme;
    writeStorageValue(THEME_KEY, theme, [THEME_KEY_LEGACY]);
  }, [theme]);

  const setSessionToken = (token) => {
    if (token) {
      writeStorageValue(TOKEN_KEY, token, [TOKEN_KEY_LEGACY]);
      api.defaults.headers.common.Authorization = `Bearer ${token}`;
      return;
    }

    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(TOKEN_KEY_LEGACY);
    delete api.defaults.headers.common.Authorization;
  };

  const resetChatState = useCallback(() => {
    setMessages([]);
    setInputText('');
    if (!onboardingAccepted) {
      setIntakeData({});
      setIntakePhase(null);
      setIntakeAccumulated({});
      setScreeningPhase('intro');
      setPhqAnswers({});
      setGadAnswers({});
      setScreeningError('');
      setWelcomeConsent(false);
    }
    setIsUserMenuOpen(false);
    setProfileNotice('');
    setProfileDraft(initialProfileDraft);
    setProfileState(null);
    setMoodDraft(initialMoodDraft);
    setJournalDraft(initialJournalDraft);
    setMoodTrend(null);
    setJournalInsights(null);
    setProfileView('profile');
    setSettingsSection('general');
    setSecurityMode('overview');
    setPasswordDraft({ current: '', next: '', confirm: '' });
    setIsProfileOpen(false);
    setSessionError('');
    setStage(onboardingAccepted ? 'chat' : 'welcome');
  }, [onboardingAccepted]);

  const clearSession = useCallback(() => {
    setSessionToken('');
    setUser(null);
    setConfig(null);
    setIsAuthenticated(false);
    setIsSidebarOpen(false);
    setAuthError('');
    setSessionError('');
    setIsAuthActive(false);
    setAuthForm(initialAuthForm);
    setHistory([]);
    setArchivedHistory([]);
    setIsArchivedChatsOpen(false);
    setSessionQuery('');
    setActiveSessionId(null);
    activeSessionIdRef.current = null;
    setNewSessionRequested(false);
    setSessionPanelError('');
    setSessionActionBusyId(null);
    setOpenSessionMenuId(null);
    setMenuPosition({ top: 0, left: 0 });
    setOnboardingAccepted(false);
    setWelcomeConsent(false);
    setIntakeData({});
    setIntakePhase(null);
    setIntakeAccumulated({});
    setScreeningPhase('intro');
    setPhqAnswers({});
    setGadAnswers({});
    setScreeningError('');
    setScreeningData(null);
    resetChatState();
  }, [resetChatState]);

  const loadHistory = useCallback(async (query = '') => {
    const trimmedQuery = query.trim();
    setSessionPanelError('');

    const [activeRes, archivedRes] = await Promise.all([
      api.get('/sessions/', {
        params: trimmedQuery ? { query: trimmedQuery, status: 'active', limit: 20 } : { status: 'active', limit: 20 },
      }),
      api.get('/sessions/', { params: { status: 'archived', limit: 20 } }),
    ]);

    setHistory(mapSessionItems(activeRes.data));
    setArchivedHistory(mapSessionItems(archivedRes.data));
  }, []);

  const loadAppData = useCallback(async () => {
    const [meRes, configRes, activeSessionsRes, archivedSessionsRes] = await Promise.all([
      api.get('/auth/me'),
      api.get('/config'),
      api.get('/sessions/', { params: { status: 'active', limit: 20 } }),
      api.get('/sessions/', { params: { status: 'archived', limit: 20 } }),
    ]);

    setUser(meRes.data);
    setConfig(configRes.data);
    setHistory(mapSessionItems(activeSessionsRes.data));
    setArchivedHistory(mapSessionItems(archivedSessionsRes.data));
    setIsArchivedChatsOpen(false);
    setIsAuthenticated(true);
    setSessionError('');
    setSessionPanelError('');
    const clinicalState = meRes.data?.clinical_state ?? {};
    const onboardingCompleted = Boolean(
      meRes.data?.onboarding_completed ?? clinicalState.onboarding_completed ?? clinicalState.screening_completed,
    );
    const screeningCompleted = Boolean(
      meRes.data?.screening_completed ?? clinicalState.screening_completed,
    );

    if (screeningCompleted || onboardingCompleted) {
      setOnboardingAccepted(true);
      setWelcomeConsent(true);
      const storedOnboarding = readOnboardingState(meRes.data?.email);
      setIntakeData(storedOnboarding?.intakeData ?? {});
      setScreeningData(storedOnboarding?.screeningData ?? null);
      setStage('chat');
    } else {
      setOnboardingAccepted(false);
      setWelcomeConsent(false);
      setIntakeData({});
      setScreeningData(null);
      setStage('welcome');
    }

    setMessages([]);
    setInputText('');
    setActiveSessionId(null);
    activeSessionIdRef.current = null;
    setNewSessionRequested(false);
    setProfileState(meRes.data?.profile ?? null);

    try {
      const [trendRes, journalRes] = await Promise.all([
        api.get('/mood/trend'),
        api.get('/journal/insights'),
      ]);
      setMoodTrend(trendRes.data);
      setJournalInsights(journalRes.data);
    } catch {
      setMoodTrend(null);
      setJournalInsights(null);
    }
  }, []);

  const bootstrapSession = useCallback(async (token) => {
    setSessionToken(token);
    await loadAppData();
  }, [loadAppData]);

  useEffect(() => {
    const storedToken = localStorage.getItem(TOKEN_KEY);

    const initialize = async () => {
      if (!storedToken) {
        setIsBootstrapping(false);
        return;
      }

      try {
        await bootstrapSession(storedToken);
      } catch (error) {
        clearSession();
        setAuthError(getErrorMessage(error, 'Session expired. Please sign in again.'));
      } finally {
        setIsBootstrapping(false);
      }
    };

    initialize();
  }, [bootstrapSession, clearSession]);

  useEffect(() => {
    if (messages.length === 0 && !isLoading) return;
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [messages, isLoading]);

  useEffect(() => {
    if (!textareaRef.current) return;
    textareaRef.current.style.height = 'auto';
    textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
  }, [inputText]);

  useEffect(() => {
    if (!isProfileOpen) return undefined;
    return undefined;
  }, [isProfileOpen]);

  useEffect(() => {
    if (!isUserMenuOpen) return undefined;

    const handlePointerDown = (event) => {
      if (!userMenuRef.current?.contains(event.target)) {
        setIsUserMenuOpen(false);
      }
    };

    document.addEventListener('pointerdown', handlePointerDown);
    return () => document.removeEventListener('pointerdown', handlePointerDown);
  }, [isUserMenuOpen]);

  useEffect(() => {
    if (openSessionMenuId === null) return undefined;

    const handlePointerDown = (event) => {
      if (!sidebarRef.current?.contains(event.target) && !sessionMenuRef.current?.contains(event.target)) {
        setOpenSessionMenuId(null);
      }
    };

    document.addEventListener('pointerdown', handlePointerDown);
    return () => document.removeEventListener('pointerdown', handlePointerDown);
  }, [openSessionMenuId]);

  const handleAuthSubmit = async (event) => {
    event.preventDefault();
    setAuthError('');
    setAuthLoading(true);

    try {
      const email = authForm.email.trim().toLowerCase();
      const password = authForm.password;

      if (!email || !password) {
        throw new Error('Email and password are required.');
      }

      if (authMode === 'register') {
        if (password !== authForm.confirmPassword) {
          throw new Error('Passwords do not match.');
        }

        await api.post('/auth/register', { email, password });
      }

      const { data } = await api.post('/auth/login', { email, password });
      setIsAuthActive(false);
      await bootstrapSession(data.access_token);
    } catch (error) {
      setAuthError(getErrorMessage(error, 'Authentication failed.'));
    } finally {
      setAuthLoading(false);
    }
  };

  const handleAuthFocusCapture = () => {
    setIsAuthActive(true);
  };

  const handleAuthBlurCapture = (event) => {
    if (!event.currentTarget.contains(event.relatedTarget)) {
      setIsAuthActive(Boolean(
        authForm.email.trim() || authForm.password.trim() || authForm.confirmPassword.trim(),
      ));
    }
  };

  const handleLogout = () => {
    setOpenSessionMenuId(null);
    setMenuPosition({ top: 0, left: 0 });
    clearSession();
  };

  useEffect(() => {
    const handleScroll = () => setOpenSessionMenuId(null);
    const sidebarContent = document.querySelector('.sidebar-content');
    sidebarContent?.addEventListener('scroll', handleScroll);
    return () => sidebarContent?.removeEventListener('scroll', handleScroll);
  }, []);

  const startNewSession = () => {
    setActiveSessionId(null);
    setNewSessionRequested(true);
    setSessionPanelError('');
    setSessionQuery('');
    setOpenSessionMenuId(null);
    setMenuPosition({ top: 0, left: 0 });
    resetChatState();
    loadHistory('').catch(() => null);
  };

  const handleSessionSearchSubmit = async (event) => {
    event.preventDefault();

    try {
      await loadHistory(sessionQuery);
      setSessionPanelError('');
    } catch (error) {
      setSessionPanelError(getErrorMessage(error, 'Sessions could not be loaded.'));
    }
  };

  const handleSessionSelect = async (sessionId) => {
    try {
      setSessionPanelError('');
      setOpenSessionMenuId(null);
      setActiveSessionId(sessionId);
      activeSessionIdRef.current = sessionId;
      const { data } = await api.get(`/sessions/${sessionId}`);
      setNewSessionRequested(false);
      setMessages((data.messages ?? []).map((message) => ({
        role: message.role,
        content: message.content,
      })));
      setIntakeData(data.intake ?? {});
      setScreeningData(null);
      setInputText('');
      setStage('chat');
      setOnboardingAccepted(true);
      setWelcomeConsent(true);
      setSessionError('');
    } catch (error) {
      setSessionPanelError(getErrorMessage(error, 'The session could not be opened.'));
    }
  };

  const handleSessionArchive = async (sessionId) => {
    try {
      setOpenSessionMenuId(null);
      setSessionActionBusyId(sessionId);
      await api.post(`/sessions/${sessionId}/archive`);
      await loadHistory(sessionQuery);
      if (String(activeSessionIdRef.current) === String(sessionId)) {
        startNewSession();
      }
    } catch (error) {
      setSessionPanelError(getErrorMessage(error, 'The session could not be archived.'));
    } finally {
      setSessionActionBusyId(null);
    }
  };

  const handleSessionDelete = async (sessionId) => {
    try {
      setOpenSessionMenuId(null);
      setSessionActionBusyId(sessionId);
      await api.delete(`/sessions/${sessionId}`);
      await loadHistory(sessionQuery);
      if (String(activeSessionIdRef.current) === String(sessionId)) {
        startNewSession();
      }
    } catch (error) {
      setSessionPanelError(getErrorMessage(error, 'The session could not be deleted.'));
    } finally {
      setSessionActionBusyId(null);
    }
  };


  const handleAssessmentStepSubmit = async (event, testType) => {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const answers = Object.fromEntries(formData.entries());
    const normalizedAnswers = Object.fromEntries(
      Object.entries(answers).map(([key, value]) => [key, Number.parseInt(value, 10)]),
    );

    if (testType === 'phq9') {
      setPhqAnswers(normalizedAnswers);
      setScreeningError('');
      setScreeningPhase('gad7');
      return;
    }

    try {
      setScreeningError('');
      setIsLoading(true);
      const phqRes = await api.post('/screen/', { test_type: 'phq9', answers: phqAnswers });
      const gadRes = await api.post('/screen/', { test_type: 'gad7', answers: normalizedAnswers });

      setScreeningData({
        scale_name: 'PHQ-9 & GAD-7',
        score: phqRes.data.score + gadRes.data.score,
        severity: `Depression: ${phqRes.data.severity} | Anxiety: ${gadRes.data.severity}`,
        crisis_flag: phqRes.data.crisis_flag || gadRes.data.crisis_flag,
        phq9: phqRes.data,
        gad7: gadRes.data,
      });
      setOnboardingAccepted(true);
      setWelcomeConsent(true);
      writeOnboardingState(user?.email, {
        completed: true,
        intakeData,
        screeningData: {
          scale_name: 'PHQ-9 & GAD-7',
          score: phqRes.data.score + gadRes.data.score,
          severity: `Depression: ${phqRes.data.severity} | Anxiety: ${gadRes.data.severity}`,
          crisis_flag: phqRes.data.crisis_flag || gadRes.data.crisis_flag,
          phq9: phqRes.data,
          gad7: gadRes.data,
        },
      });
      setStage('chat');
    } catch (error) {
      if (isUnauthorized(error)) {
        handleLogout();
        return;
      }
      
      const serverMsg = error?.response?.data?.detail;
      const errorMsg = serverMsg ? `Error: ${serverMsg}` : (error?.message === 'Network Error' ? 'Bağlantı Hatası: Sunucuya ulaşılamıyor veya CORS engeli var.' : error.message);
      setScreeningError(errorMsg);
    } finally {
      setIsLoading(false);
    }
  };

  const handleScreeningAnswerChange = (testType, questionId, value) => {
    const parsedValue = Number.parseInt(value, 10);

    if (testType === 'phq9') {
      setPhqAnswers((prev) => ({ ...prev, [questionId]: parsedValue }));
      return;
    }

    setGadAnswers((prev) => ({ ...prev, [questionId]: parsedValue }));
  };

  const openProfilePanel = () => {
    setProfileDraft({
      displayName: profileState?.preferred_name || displayName,
      username: user?.username || user?.email?.split('@')[0] || displayName.toLowerCase().replace(/\s+/g, ''),
      mainTriggers: profileState?.main_triggers || '',
      supportSystem: profileState?.support_system || '',
      helpfulCoping: profileState?.coping_strategies_helpful || '',
      communicationStyle: profileState?.communication_style || 'Warm_and_Gentle',
      responseLengthPreference: profileState?.response_length_preference || 'Balanced',
      goalsForSupport: profileState?.goals_for_support || 'Emotional_Support',
      useMoodContext: Boolean(profileState?.use_mood_context),
      useJournalContext: Boolean(profileState?.use_journal_context),
      useMemoryContext: profileState?.use_memory_context ?? true,
    });
    setProfileNotice('');
    setProfileView('profile');
    setSettingsSection('general');
    setSecurityMode('overview');
    setPasswordDraft({ current: '', next: '', confirm: '' });
    setIsUserMenuOpen(false);
    setIsProfileOpen(true);
  };

  const handleProfileSave = async (event) => {
    event.preventDefault();

    if (profileView !== 'profile') {
      setProfileNotice('This section now syncs through its own controls below.');
      return;
    }

    try {
      const payload = {
        preferred_name: profileDraft.displayName,
        main_triggers: profileDraft.mainTriggers,
        support_system: profileDraft.supportSystem,
        coping_strategies_helpful: profileDraft.helpfulCoping,
        communication_style: profileDraft.communicationStyle,
        response_length_preference: profileDraft.responseLengthPreference,
        goals_for_support: profileDraft.goalsForSupport,
        use_mood_context: profileDraft.useMoodContext,
        use_journal_context: profileDraft.useJournalContext,
        use_memory_context: profileDraft.useMemoryContext,
      };
      const { data } = await api.put('/profile/', payload);
      setProfileState(data);
      setIntakeData((prev) => ({
        ...prev,
        profile_display_name: profileDraft.displayName,
        profile_username: profileDraft.username,
        communication_style: profileDraft.communicationStyle,
        response_length_preference: profileDraft.responseLengthPreference,
        help_type: profileDraft.goalsForSupport,
      }));
      setProfileNotice(`Profile updated. ${APP_NAME} will use this revised context in future responses.`);
    } catch (error) {
      setProfileNotice(getErrorMessage(error, 'Profile could not be updated.'));
    }
  };

  const handleMoodSave = async () => {
    try {
      await api.post('/mood/', moodDraft);
      const { data } = await api.get('/mood/trend');
      setMoodTrend(data);
      setMoodDraft(initialMoodDraft);
      setProfileNotice('Mood check-in saved.');
    } catch (error) {
      setProfileNotice(getErrorMessage(error, 'Mood check-in could not be saved.'));
    }
  };

  const handleJournalSave = async () => {
    try {
      await api.post('/journal/', journalDraft);
      const { data } = await api.get('/journal/insights');
      setJournalInsights(data);
      setJournalDraft(initialJournalDraft);
      setProfileNotice('Journal entry saved.');
    } catch (error) {
      setProfileNotice(getErrorMessage(error, 'Journal entry could not be saved.'));
    }
  };

  const handleArchiveAllChats = () => {
    setHistory([]);
    setMessages([]);
    setProfileNotice('Tum sohbetler arsivlendi. Gecmis listesi temizlendi.');
  };

  const handleWelcomeContinue = () => {
    if (!welcomeConsent) {
      setSessionError('Please accept the consent to continue with the intake and assessments.');
      return;
    }

    setSessionError('');

    // Start conversational intake inside the chat
    const firstQuestion = config?.first_intake_question
      || "Welcome! I'm glad you're here. Before we begin, I'd like to get to know you a little better. Could you tell me what name you'd like me to call you?";

    setMessages([{ role: 'assistant', content: firstQuestion }]);
    setIntakePhase('name');
    setIntakeAccumulated({});
    setStage('chat');
  };

  const handleReviseIntake = () => {
    setProfileNotice('');
    setIsProfileOpen(false);

    const firstQuestion = config?.first_intake_question
      || "Welcome! I'm glad you're here. Before we begin, I'd like to get to know you a little better. Could you tell me what name you'd like me to call you?";

    setMessages([{ role: 'assistant', content: firstQuestion }]);
    setIntakePhase('name');
    setIntakeAccumulated({});
    setStage('chat');
  };

  const handleReviseAssessments = () => {
    setProfileNotice('');
    setIsProfileOpen(false);
    setScreeningPhase('phq9');
    setStage('screening');
  };

  const handleDeleteAllChats = () => {
    setHistory([]);
    setMessages([]);
    setInputText('');
    setProfileNotice('Tum sohbetler silindi.');
  };

  const handlePasswordSave = (event) => {
    event.preventDefault();

    if (!passwordDraft.current || !passwordDraft.next || !passwordDraft.confirm) {
      setProfileNotice('Parola guncellemek icin tum alanlari doldur.');
      return;
    }

    if (passwordDraft.next !== passwordDraft.confirm) {
      setProfileNotice('Yeni parola ve tekrar alanlari eslesmiyor.');
      return;
    }

    setProfileNotice('Parola guncelleme akisi hazir. Backend baglantisini bir sonraki adimda tamamlayabiliriz.');
    setPasswordDraft({ current: '', next: '', confirm: '' });
    setSecurityMode('overview');
  };
  // ------------------------------------------------------------------
  // Conversational Intake Step Handler
  // ------------------------------------------------------------------
  const submitIntakeStep = async (text) => {
    if (!text.trim() || isLoading) return;

    const userMsg = { role: 'user', content: text };
    setMessages((prev) => [...prev, userMsg]);
    setInputText('');
    setIsLoading(true);
    setSessionError('');

    try {
      const { data } = await api.post('/chat/intake-step/', {
        phase: intakePhase,
        answer: text,
        accumulated: intakeAccumulated,
      });

      if (data.safety_alert) {
        // Crisis detected! Show alert and stop intake.
        setMessages((prev) => [
          ...prev,
          { role: 'assistant', content: data.safety_alert, data: { safety_alert: true } },
        ]);
        setIntakePhase(null);
        setIsLoading(false);
        return;
      }

      setIntakeAccumulated(data.extracted || {});

      if (data.complete) {
        // Intake is done — save extracted data and move to screening
        setIntakeAccumulated(data.extracted || {});
        setIntakeData(data.extracted || {});
        setIntakePhase(null);

        const messagesToAdd = [];
        if (data.reflection) {
          messagesToAdd.push({ role: 'assistant', content: data.reflection });
        }
        messagesToAdd.push({
          role: 'assistant',
          content:
            'This initial understanding helps me hold a safe and supportive space for you. ' +
            'To further refine our starting point, I would like to offer two standard screening questionnaires (PHQ-9 and GAD-7). ' +
            'These are not diagnostic tools on their own, but they provide a baseline for tracking patterns and keeping guidance appropriately bounded.',
        });

        setMessages((prev) => [...prev, ...messagesToAdd]);

        // Transition to screening after a longer delay so user can read the summary
        setTimeout(() => {
          setOnboardingAccepted(false);
          setScreeningPhase('phq9');
          setPhqAnswers({});
          setGadAnswers({});
          setScreeningError('');
          setStage('screening');
        }, 4500);
      } else if (data.next_question) {
        // Show the reflection and then the next intake question
        setIntakePhase(data.next_phase);
        const messagesToAdd = [];
        if (data.reflection) {
          messagesToAdd.push({ role: 'assistant', content: data.reflection });
        }
        messagesToAdd.push({ role: 'assistant', content: data.next_question });
        setMessages((prev) => [...prev, ...messagesToAdd]);
      }
    } catch (error) {
      if (isUnauthorized(error)) {
        handleLogout();
        return;
      }
      setSessionError(getErrorMessage(error, 'Could not process your response. Please try again.'));
    } finally {
      setIsLoading(false);
    }
  };

  const submitMessage = async (text) => {
    if (!text.trim() || isLoading) return;

    const userMsg = { role: 'user', content: text };
    const nextMessages = [...messages, userMsg];
    const payloadHistory = nextMessages.map((message) => ({
      role: message.role,
      content: message.content,
    }));

    setMessages(nextMessages);
    setInputText('');
    setIsLoading(true);
    setSessionError('');

    try {
      const response = await api.post('/chat/', {
        message: text,
        intake: intakeData,
        screening: screeningData ?? {},
        history: payloadHistory,
        session_id: activeSessionId,
        new_session: newSessionRequested,
        personalization: {
          preferred_name: profileState?.preferred_name || profileDraft.displayName || '',
          main_triggers: profileState?.main_triggers || profileDraft.mainTriggers || '',
          support_system: profileState?.support_system || profileDraft.supportSystem || '',
          coping_strategies_helpful: profileState?.coping_strategies_helpful || profileDraft.helpfulCoping || '',
          personalization_consent: profileState?.personalization_consent ?? true,
          use_mood_context: profileState?.use_mood_context ?? profileDraft.useMoodContext,
          use_journal_context: profileState?.use_journal_context ?? profileDraft.useJournalContext,
          use_memory_context: profileState?.use_memory_context ?? profileDraft.useMemoryContext,
        },
      });

      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: response.data.answer,
          data: response.data,
          personalization: response.data.personalization_signals ?? [],
        },
      ]);
      setActiveSessionId(response.data.session_id ?? activeSessionId);
      activeSessionIdRef.current = response.data.session_id ?? activeSessionId;
      setNewSessionRequested(false);
      await loadHistory(sessionQuery).catch(() => null);
    } catch (error) {
      if (isUnauthorized(error)) {
        handleLogout();
        return;
      }

      setSessionError(getErrorMessage(error, 'The assistant could not respond.'));
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: 'The support assistant is currently unavailable. Please try again.',
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSendMessage = (event) => {
    event.preventDefault();
    if (intakePhase) {
      submitIntakeStep(inputText);
    } else {
      submitMessage(inputText);
    }
  };

  const handleKeyDown = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSendMessage(event);
    }
  };

  const isPreviewMode = !isAuthenticated;
  const shouldShowWelcomeOverlay = isAuthenticated && stage === 'welcome';
  const shouldShowScreeningOverlay = isAuthenticated && stage === 'screening';
  const displayName = formatDisplayName(user);
  const profileAvatarText = (profileDraft.displayName || displayName)
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join('') || 'U';
  const screeningStepMeta = {
    phq9: {
      badge: 'Step 1 of 2',
      title: 'PHQ-9 Depression Assessment',
      description: 'Answer based on how you have felt during the last two weeks.',
      questions: config?.phq9_questions ?? [],
      values: phqAnswers,
      submitLabel: 'Continue to GAD-7',
    },
    gad7: {
      badge: 'Step 2 of 2',
      title: 'GAD-7 Anxiety Assessment',
      description: 'This second assessment helps us understand your current anxiety baseline.',
      questions: config?.gad7_questions ?? [],
      values: gadAnswers,
      submitLabel: isLoading ? 'Analyzing baseline...' : 'Complete Assessment',
    },
  };

  if (isBootstrapping) {
    return (
      <div className="center-overlay">
        <div className="text-center">
          <Sparkles className="pulse text-accent mb-4" size={48} />
          <h2 className="text-2xl font-semibold">Initializing secure session...</h2>
        </div>
      </div>
    );
  }

  return (
    <div className={`app-shell ${isPreviewMode ? 'app-shell--locked' : ''}`}>
      <div className="app-layout">
      <aside ref={sidebarRef} className={`sidebar ${isSidebarOpen ? 'open' : ''}`}>
        <div className="sidebar-header">
          <div className="sidebar-header-top">
            <div className="sidebar-brand">
            <span>{APP_NAME}</span>
            </div>
            <button 
              type="button" 
              className="sidebar-toggle-btn" 
              onClick={() => setIsSidebarOpen(false)}
              title="Close sidebar"
            >
              <PanelLeft size={24} />
            </button>
          </div>
          
          <div className="sidebar-actions">
            <button type="button" className="sidebar-action-btn" onClick={startNewSession}>
              <SquarePen size={22} />
              <span>Yeni sohbet</span>
            </button>
            <form className="sidebar-search" onSubmit={handleSessionSearchSubmit}>
              <input
                type="search"
                className="sidebar-search__input"
                placeholder="Search sessions..."
                value={sessionQuery}
                onChange={(event) => setSessionQuery(event.target.value)}
              />
              <button type="submit" className="sidebar-search__button" title="Search sessions">
                <Search size={20} />
              </button>
              {sessionQuery && (
                <button
                  type="button"
                  className="sidebar-search__button sidebar-search__button--ghost"
                  onClick={() => {
                    setSessionQuery('');
                    loadHistory('').catch(() => null);
                  }}
                  title="Clear search"
                >
                  <X size={20} />
                </button>
              )}
            </form>
            {sessionPanelError && <div className="sidebar-inline-error">{sessionPanelError}</div>}
          </div>
        </div>

        <div className="sidebar-content">
          <div className={`sidebar-archive-section ${isArchivedChatsOpen ? 'is-open' : ''}`}>
            <div className="sidebar-archive-section__header">
              <span className="sidebar-archive-section__label">Archived chats</span>
              <button
                type="button"
                className="sidebar-archive-section__toggle"
                onClick={() => setIsArchivedChatsOpen((current) => !current)}
                aria-label={isArchivedChatsOpen ? 'Collapse archived chats' : 'Expand archived chats'}
                aria-expanded={isArchivedChatsOpen}
              >
                <ChevronDown size={16} className="sidebar-archive-section__chevron" />
              </button>
            </div>

            <div className="sidebar-archive-section__body">
              {archivedHistory.length > 0 ? (
                archivedHistory.map((item) => (
                  <div
                    key={item.id}
                    className={`history-item is-archived ${activeSessionId === item.id ? 'active' : ''}`}
                  >
                    <button type="button" className="history-item__main" onClick={() => handleSessionSelect(item.id)}>
                      <span className="history-item-title">{item.title}</span>
                    </button>
                    <div className="history-item__actions">
                      <button
                        type="button"
                        className="history-item__action-btn history-item__action-btn--menu"
                        onClick={(event) => {
                          event.stopPropagation();
                          if (openSessionMenuId === item.id) {
                            setOpenSessionMenuId(null);
                            return;
                          }

                          const rect = event.currentTarget.getBoundingClientRect();
                          const menuWidth = 176;
                          const viewportPadding = 12;
                          const top = Math.min(rect.bottom + 8, window.innerHeight - 124);
                          const left = Math.max(
                            viewportPadding,
                            Math.min(rect.right - 36, window.innerWidth - menuWidth - viewportPadding),
                          );

                          setMenuPosition({ top, left });
                          setOpenSessionMenuId(item.id);
                        }}
                        title="Session actions"
                        aria-expanded={openSessionMenuId === item.id}
                      >
                        <MoreHorizontal size={48} />
                      </button>
                    </div>
                  </div>
                ))
              ) : (
                <div className="history-empty">No archived chats yet.</div>
              )}
            </div>
          </div>

          <div className="sidebar-section-label">Chats</div>
          {history.length > 0 ? (
            history.map((item) => (
              <div
                key={item.id}
                className={`history-item ${activeSessionId === item.id ? 'active' : ''}`}
              >
                <button type="button" className="history-item__main" onClick={() => handleSessionSelect(item.id)}>
                  <span className="history-item-title">{item.title}</span>
                </button>
                <div className="history-item__actions">
                  <button
                    type="button"
                    className="history-item__action-btn history-item__action-btn--menu"
                    onClick={(event) => {
                      event.stopPropagation();
                      if (openSessionMenuId === item.id) {
                        setOpenSessionMenuId(null);
                        return;
                      }

                      const rect = event.currentTarget.getBoundingClientRect();
                      const menuWidth = 176;
                      const viewportPadding = 12;
                      const top = Math.min(rect.bottom + 8, window.innerHeight - 124);
                      const left = Math.max(
                        viewportPadding,
                        Math.min(rect.right - 36, window.innerWidth - menuWidth - viewportPadding),
                      );

                      setMenuPosition({ top, left });
                      setOpenSessionMenuId(item.id);
                    }}
                    title="Session actions"
                    aria-expanded={openSessionMenuId === item.id}
                  >
                    <MoreHorizontal size={48} />
                  </button>
                </div>
              </div>
            ))
          ) : (
            <div className="history-empty">No active chats yet.</div>
          )}
        </div>

        <div className="sidebar-footer">
          <div ref={userMenuRef} className="sidebar-user-menu">
            <button
              type="button"
              className="sidebar-profile"
              onClick={() => setIsUserMenuOpen((current) => !current)}
            >
              <div className="sidebar-profile__avatar" aria-hidden="true" />
              <span>{displayName}</span>
            </button>

            {isUserMenuOpen && (
              <div className="sidebar-user-menu__panel">
                <button type="button" className="sidebar-user-menu__item" onClick={() => { openProfilePanel(); setProfileView('profile'); }}>
                  <User size={20} />
                  Profile
                </button>
                <button type="button" className="sidebar-user-menu__item" onClick={() => { openProfilePanel(); setProfileView('personalization'); }}>
                  <SlidersHorizontal size={20} />
                  Personalization
                </button>
                <button type="button" className="sidebar-user-menu__item" onClick={() => { openProfilePanel(); setProfileView('settings'); setSettingsSection('general'); }}>
                  <Settings size={20} />
                  Settings
                </button>
                <div className="sidebar-user-menu__item sidebar-user-menu__item--has-sub">
                  <div className="sidebar-user-menu__item-main">
                    <LifeBuoy size={20} />
                    <span>Help & legal</span>
                  </div>
                  <ChevronRight size={16} />
                  
                  <div className="sidebar-user-menu__sub">
                    <button type="button" className="sidebar-user-menu__sub-item" onClick={() => { openProfilePanel(); setProfileView('help'); }}>
                      <CircleHelp size={18} />
                      <span>Help Center</span>
                    </button>
                    <button type="button" className="sidebar-user-menu__sub-item">
                      <ClipboardList size={18} />
                      <span>Release Notes</span>
                    </button>
                    <div className="sidebar-user-menu__sub-divider" />
                    <button type="button" className="sidebar-user-menu__sub-item">
                      <FileText size={18} />
                      <span>Terms of Service</span>
                    </button>
                    <button type="button" className="sidebar-user-menu__sub-item">
                      <ShieldCheck size={18} />
                      <span>Privacy Policy</span>
                    </button>
                    <button type="button" className="sidebar-user-menu__sub-item">
                      <LifeBuoy size={18} />
                      <span>Report a Bug</span>
                    </button>
                  </div>
                </div>
                <div className="sidebar-user-menu__divider" />
                <button type="button" className="sidebar-user-menu__item is-danger" onClick={handleLogout}>
                  <LogOut size={20} />
                  Log out
                </button>
              </div>
            )}
          </div>
        </div>
      </aside>

      <main className="main-content">
        <button type="button" className="mobile-menu-toggle mobile-menu-toggle--floating" onClick={() => setIsSidebarOpen(!isSidebarOpen)}>
          {isSidebarOpen ? <X /> : <Menu />}
        </button>

        {!isSidebarOpen && (
          <button 
            type="button" 
            className="sidebar-open-btn" 
            onClick={() => setIsSidebarOpen(true)}
            title="Open sidebar"
          >
            <PanelLeft size={20} />
          </button>
        )}

        {sessionError && <div className="session-banner">{sessionError}</div>}

        <section className="chat-viewport">
          <div className="chat-max-width">
            {messages.length === 0 && (stage === 'chat' || isPreviewMode) && (
              <div className="empty-state animate-fade-in">
                <div className="empty-state-icon">
                  <Brain size={30} className="text-accent" />
                </div>
                <h2>{isPreviewMode ? `${APP_NAME} is waiting for you.` : 'What shall we talk about?'}</h2>
                <p>
                  {isPreviewMode
                    ? 'Chat area is ready. Please log in to your secure session to continue.'
                    : 'Keep it short, and I will answer clearly.'}
                </p>
              </div>
            )}

            {messages.map((msg, idx) => (
              msg.role === 'user' ? (
                <div key={idx} className="message-row user">
                  <div className="message-content">
                    <div className="font-semibold text-xs mb-1 uppercase tracking-wider text-muted">
                      You
                    </div>
                    <div className="prose prose-invert max-w-none text-slate-200">{msg.content}</div>
                  </div>
                  <div className="avatar avatar-user" aria-hidden="true">
                    <User size={18} />
                  </div>
                </div>
              ) : (
                <div key={idx} className="message-row assistant">
                  <div className="avatar avatar-assistant" aria-hidden="true">
                    <Sparkles size={18} />
                  </div>
                  <div className="message-content">
                    <div className="font-semibold text-xs mb-1 uppercase tracking-wider text-muted">
                      {intakePhase ? `${APP_NAME} Support Intake` : `${APP_NAME} (AI)`}
                    </div>
                    {msg.data?.status === 'crisis' && (
                      <div className="crisis-alert">
                        <div className="flex items-center gap-2 mb-2 font-bold">
                          <AlertTriangle size={18} />
                          CRISIS PROTOCOL DETECTED
                        </div>
                        We detected content that suggests you might be in immediate danger. Please contact your local
                        emergency services or a crisis hotline immediately.
                      </div>
                    )}
                    <div className="prose prose-invert max-w-none text-slate-200">{msg.content}</div>

                    {msg.data?.clinical_nugget && (
                      <div className="clinical-nugget-card animate-slide-up">
                        <div className="flex items-center gap-2 text-xs font-bold text-accent mb-2 tracking-widest uppercase">
                          <Lightbulb size={14} />
                          Psychoeducation Insight
                        </div>
                        <div className="text-sm text-slate-300 leading-relaxed italic">
                          "{msg.data.clinical_nugget}"
                        </div>
                      </div>
                    )}

                    {msg.data?.source_highlight && (
                      <div className="mt-3 rounded-2xl border border-accent/20 bg-accent/5 px-4 py-3 text-sm text-slate-200">
                        <div className="text-[10px] font-bold uppercase tracking-[0.24em] text-accent mb-1">
                          Primary evidence
                        </div>
                        <div className="font-medium">{msg.data.source_highlight}</div>
                      </div>
                    )}

                    {msg.data?.sources?.length > 0 && (
                      <div className="mt-4 pt-4 border-t border-white/5">
                        <div className="flex items-center gap-2 text-xs font-semibold text-muted mb-2">
                          <FileText size={14} />
                          SUPPORT SOURCES
                        </div>
                        <div className="flex flex-wrap gap-2">
                          {msg.data.sources.map((src, sidx) => (
                            <div key={sidx} className="source-tag">
                              <div className="font-semibold">{src.title}</div>
                              <div className="text-[11px] text-muted mt-1">
                                {src.source}
                                {src.section ? ` · ${src.section}` : ''}
                                {src.page ? ` · p.${src.page}` : ''}
                              </div>
                              <div className="mt-1 flex flex-wrap gap-1 text-[10px] text-muted uppercase tracking-wide">
                                {src.source_kind && <span>{src.source_kind.replace(/_/g, ' ')}</span>}
                                {src.language && <span>{src.language}</span>}
                                {typeof src.confidence === 'number' && <span>conf {src.confidence.toFixed(2)}</span>}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )
            ))}

            {isLoading && (
              <div className="message-row assistant">
                <div className="avatar avatar-assistant">
                  <Sparkles size={18} className="animate-spin" />
                </div>
                <div className="message-content text-muted italic flex items-center gap-2">
                  {intakePhase ? 'Calma is reflecting...' : 'Searching support index...'}
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </section>

        <footer className="input-area-wrapper">
          <form className="input-container" onSubmit={handleSendMessage}>
            <textarea
              ref={textareaRef}
              rows="1"
              className="chat-textarea"
              placeholder={intakePhase ? 'Type your answer...' : `Message ${APP_NAME}...`}
              value={inputText}
              onChange={(event) => setInputText(event.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isLoading || stage !== 'chat'}
            />
            <button type="submit" className="send-btn" disabled={isLoading || !inputText.trim() || stage !== 'chat'}>
              <Send size={18} />
            </button>
          </form>
          <div className="text-center mt-3">
            <p className="text-[10px] text-muted tracking-wide">
              {APP_NAME} can make mistakes. Verify important medical info. Not for emergencies.
            </p>
          </div>
        </footer>

        {shouldShowWelcomeOverlay && (
          <div className="center-overlay">
            <div className="glass-card welcome-card animate-fade-in text-center">
              <div className="welcome-icon">
                <Brain className="text-accent" size={30} />
              </div>
              <p className="welcome-kicker">{APP_NAME}</p>
              <h2>Let&apos;s begin.</h2>
              <p className="welcome-copy">
                Let&apos;s get to know each other. I am {APP_NAME}; trained by students to provide psychological awareness
                and information. I will be your companion, but first, I need your consent for a few short questions
                and assessments.
              </p>

              <div className="welcome-consent">
                <input
                  id="welcome-consent"
                  type="checkbox"
                  className="screening-consent__checkbox"
                  checked={welcomeConsent}
                  onChange={(event) => setWelcomeConsent(event.target.checked)}
                />
                <label htmlFor="welcome-consent" className="welcome-consent__label">
                  I consent to the intake questions and PHQ-9 / GAD-7 assessments to personalize the chat experience.
                </label>
              </div>

              {sessionError && <div className="screening-inline-error">{sessionError}</div>}

              <button type="button" className="btn-primary w-full mt-6 py-4" onClick={handleWelcomeContinue}>
                Continue
              </button>
            </div>
          </div>
        )}


        {shouldShowScreeningOverlay && (
          <div className="center-overlay bg-black/60 backdrop-blur-md">
            <div className="glass-card screening-card">
              <form
                className="screening-form"
                onSubmit={(event) => handleAssessmentStepSubmit(event, screeningPhase)}
              >
                  <div className="screening-form__header">
                    <div>
                      <p className="screening-form__badge">{screeningStepMeta[screeningPhase].badge}</p>
                      <h2 className="screening-form__title">{screeningStepMeta[screeningPhase].title}</h2>
                      <p className="screening-form__copy">{screeningStepMeta[screeningPhase].description}</p>
                    </div>
                    <div className="screening-form__progress">
                      {screeningPhase === 'phq9' ? '9 questions' : '7 questions'}
                    </div>
                  </div>

                  <div className="screening-question-list">
                    {screeningStepMeta[screeningPhase].questions.map((question, questionIndex) => (
                      <div key={question.id} className="screening-question-card">
                        <div className="screening-question-card__head">
                          <span className="screening-question-card__index">{questionIndex + 1}</span>
                          <p className="screening-question-card__text">{question.text}</p>
                        </div>
                        <div className="screening-option-grid">
                          {config?.response_options.map((option, index) => (
                            <label
                              key={option}
                              className={`screening-option ${
                                screeningStepMeta[screeningPhase].values[question.id] === index ? 'is-selected' : ''
                              }`}
                            >
                              <input
                                type="radio"
                                required
                                name={question.id}
                                value={index}
                                checked={screeningStepMeta[screeningPhase].values[question.id] === index}
                                onChange={(event) =>
                                  handleScreeningAnswerChange(screeningPhase, question.id, event.target.value)}
                              />
                              <span className="screening-option__control" />
                              <span className="screening-option__label">{option}</span>
                            </label>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>

                  {screeningError && <div className="screening-inline-error">{screeningError}</div>}

                  <div className="screening-form__footer">
                    {screeningPhase === 'gad7' && (
                      <button
                        type="button"
                        className="screening-form__back"
                        onClick={() => setScreeningPhase('phq9')}
                        disabled={isLoading}
                      >
                        Back to PHQ-9
                      </button>
                    )}
                    <button type="submit" className="btn-primary screening-card__submit" disabled={isLoading}>
                      {isLoading ? (
                        <>
                          <Sparkles className="animate-spin" /> Analyzing baseline...
                        </>
                      ) : (
                        screeningStepMeta[screeningPhase].submitLabel
                      )}
                    </button>
                  </div>
              </form>
            </div>
          </div>
        )}
      </main>
      </div>

      {isPreviewMode && (
        <div className={`auth-overlay ${isAuthActive ? 'is-active' : ''}`}>
          <div className="auth-overlay__scrim" />
          <div className="auth-stage__ambient auth-stage__ambient--one" />
          <div className="auth-stage__ambient auth-stage__ambient--two" />
          <div className="auth-stage__ambient auth-stage__ambient--three" />

          <div className={`glass-card auth-card--immersive ${isAuthActive ? 'is-active' : ''}`}>
            <div className="auth-card-header">
              <div>
                <h2>{authMode === 'login' ? 'Sign in' : 'Create account'}</h2>
                <p>
                  {authMode === 'login'
                    ? 'Log in to continue.'
                    : 'Create your account in minutes.'}
                </p>
              </div>
              <button
                type="button"
                className="auth-mode-toggle"
                onClick={() => {
                  setAuthError('');
                  setIsAuthActive(false);
                  setAuthMode(authMode === 'login' ? 'register' : 'login');
                }}
              >
                {authMode === 'login' ? <UserPlus size={16} /> : <LogIn size={16} />}
                {authMode === 'login' ? 'Register' : 'Sign in'}
              </button>
            </div>

            {authError && <div className="auth-error">{authError}</div>}

            <form
              className="auth-form"
              onSubmit={handleAuthSubmit}
              onFocusCapture={handleAuthFocusCapture}
              onBlurCapture={handleAuthBlurCapture}
            >
              <label>
                <span>
                  <Mail size={14} /> Email
                </span>
                <input
                  className="form-input"
                  type="email"
                  value={authForm.email}
                  onChange={(event) => {
                    setIsAuthActive(true);
                    setAuthForm((prev) => ({ ...prev, email: event.target.value }));
                  }}
                  required
                  autoComplete="email"
                  placeholder="example@mail.com"
                />
              </label>

              <label>
                <span>
                  <KeyRound size={14} /> Password
                </span>
                <input
                  className="form-input"
                  type="password"
                  value={authForm.password}
                  onChange={(event) => {
                    setIsAuthActive(true);
                    setAuthForm((prev) => ({ ...prev, password: event.target.value }));
                  }}
                  required
                  autoComplete={authMode === 'login' ? 'current-password' : 'new-password'}
                  minLength={8}
                  placeholder="At least 8 characters"
                />
              </label>

              {authMode === 'register' && (
                <label>
                  <span>
                    <KeyRound size={14} /> Confirm password
                  </span>
                  <input
                    className="form-input"
                    type="password"
                    value={authForm.confirmPassword}
                    onChange={(event) => {
                      setIsAuthActive(true);
                      setAuthForm((prev) => ({ ...prev, confirmPassword: event.target.value }));
                    }}
                    required
                    autoComplete="new-password"
                    minLength={8}
                    placeholder="Repeat your password"
                  />
                </label>
              )}

              <button type="submit" className="btn-primary w-full py-4" disabled={authLoading}>
                {authLoading ? 'Please wait...' : authMode === 'login' ? 'Sign in' : 'Create account'}
              </button>
            </form>
          </div>
        </div>
      )}

        {isAuthenticated && isProfileOpen && (
          <div className="profile-overlay">
          <div className="profile-overlay__scrim" onClick={() => setIsProfileOpen(false)} />
          <div
            ref={profilePanelRef}
            className={`glass-card profile-panel profile-panel--${profileView}`}
          >
            <div className="profile-panel__header">
              <h2 className="settings-section-title-header">
                {profileView === 'settings' ? (
                  settingsSection === 'general' ? 'General' :
                  settingsSection === 'data-controls' ? 'Data controls' :
                  settingsSection === 'security' ? 'Security' :
                  settingsSection === 'account' ? 'Account' : ''
                ) : (
                  profileView === 'profile'
                    ? 'Profile'
                    : profileView === 'personalization'
                      ? 'Personalization'
                      : 'Help'
                )}
              </h2>
              {profileView === 'settings' && (
                <button type="button" className="profile-panel__close" onClick={() => setIsProfileOpen(false)}>
                  <X size={18} />
                </button>
              )}
            </div>

            <form className="profile-panel__body" onSubmit={handleProfileSave}>
              {profileView === 'profile' && (
                <>
                  <section className="profile-editor-hero">
                    <div className="profile-editor-hero__avatar">{profileAvatarText}</div>
                    <button type="button" className="profile-editor-hero__camera" aria-label="Change avatar">
                      <Camera size={16} />
                    </button>
                  </section>

                  <section className="profile-editor-fields">
                    <label className="profile-editor-field">
                      <span>Display name</span>
                      <input
                        className="form-input"
                        placeholder="Your name"
                        value={profileDraft.displayName}
                        onChange={(event) =>
                          setProfileDraft((prev) => ({ ...prev, displayName: event.target.value }))
                        }
                      />
                    </label>

                    <label className="profile-editor-field">
                      <span>Username</span>
                      <input
                        className="form-input"
                        placeholder="username"
                        value={profileDraft.username}
                        onChange={(event) =>
                          setProfileDraft((prev) => ({ ...prev, username: event.target.value }))
                        }
                      />
                    </label>

                    <label className="profile-editor-field">
                      <span>Main triggers</span>
                      <input
                        className="form-input"
                        placeholder="Exams, sleep loss, family pressure..."
                        value={profileDraft.mainTriggers}
                        onChange={(event) =>
                          setProfileDraft((prev) => ({ ...prev, mainTriggers: event.target.value }))
                        }
                      />
                    </label>

                    <label className="profile-editor-field">
                      <span>Support system</span>
                      <input
                        className="form-input"
                        placeholder="Friends, family, counselor..."
                        value={profileDraft.supportSystem}
                        onChange={(event) =>
                          setProfileDraft((prev) => ({ ...prev, supportSystem: event.target.value }))
                        }
                      />
                    </label>

                    <label className="profile-editor-field">
                      <span>Helpful coping strategies</span>
                      <input
                        className="form-input"
                        placeholder="Breathing, journaling, short plans..."
                        value={profileDraft.helpfulCoping}
                        onChange={(event) =>
                          setProfileDraft((prev) => ({ ...prev, helpfulCoping: event.target.value }))
                        }
                      />
                    </label>

                    <label className="profile-editor-field">
                      <span>Communication style</span>
                      <select
                        className="form-input"
                        value={profileDraft.communicationStyle}
                        onChange={(event) =>
                          setProfileDraft((prev) => ({ ...prev, communicationStyle: event.target.value }))
                        }
                      >
                        <option value="Warm_and_Gentle">Warm and gentle</option>
                        <option value="Direct_and_Practical">Direct and practical</option>
                        <option value="Structured_and_Analytical">Structured and analytical</option>
                      </select>
                    </label>

                    <label className="profile-editor-field">
                      <span>Response length</span>
                      <select
                        className="form-input"
                        value={profileDraft.responseLengthPreference}
                        onChange={(event) =>
                          setProfileDraft((prev) => ({ ...prev, responseLengthPreference: event.target.value }))
                        }
                      >
                        <option value="Very_Short">Very short</option>
                        <option value="Balanced">Balanced</option>
                        <option value="Detailed">Detailed</option>
                      </select>
                    </label>

                    <label className="profile-editor-field">
                      <span>Support goal</span>
                      <select
                        className="form-input"
                        value={profileDraft.goalsForSupport}
                        onChange={(event) =>
                          setProfileDraft((prev) => ({ ...prev, goalsForSupport: event.target.value }))
                        }
                      >
                        <option value="Practical_Coping_Steps">Practical coping steps</option>
                        <option value="Source_Backed_Explanation">Source-backed explanation</option>
                        <option value="Emotional_Support">Emotional support</option>
                        <option value="Reflection_and_Self_Understanding">Reflection and self-understanding</option>
                      </select>
                    </label>

                    <label className="profile-editor-field">
                      <span className="flex items-center justify-between">
                        <span>Use mood trend in chat</span>
                        <input
                          type="checkbox"
                          checked={profileDraft.useMoodContext}
                          onChange={(event) =>
                            setProfileDraft((prev) => ({ ...prev, useMoodContext: event.target.checked }))
                          }
                        />
                      </span>
                    </label>

                    <label className="profile-editor-field">
                      <span className="flex items-center justify-between">
                        <span>Use journal insight in chat</span>
                        <input
                          type="checkbox"
                          checked={profileDraft.useJournalContext}
                          onChange={(event) =>
                            setProfileDraft((prev) => ({ ...prev, useJournalContext: event.target.checked }))
                          }
                        />
                      </span>
                    </label>

                    </section>
                  </>
                )}

              {profileView === 'settings' && (
                <section className="settings-layout">
                  <div className="settings-nav">
                    <button
                      type="button"
                      className={`profile-menu-section ${settingsSection === 'general' ? 'is-active' : ''}`}
                      onClick={() => setSettingsSection('general')}
                    >
                      <SlidersHorizontal size={18} />
                      General
                    </button>
                    <button
                      type="button"
                      className={`profile-menu-section ${settingsSection === 'data-controls' ? 'is-active' : ''}`}
                      onClick={() => setSettingsSection('data-controls')}
                    >
                      <Database size={18} />
                      Data controls
                    </button>
                    <button
                      type="button"
                      className={`profile-menu-section ${settingsSection === 'security' ? 'is-active' : ''}`}
                      onClick={() => setSettingsSection('security')}
                    >
                      <Shield size={18} />
                      Security
                    </button>
                    <button
                      type="button"
                      className={`profile-menu-section ${settingsSection === 'account' ? 'is-active' : ''}`}
                      onClick={() => setSettingsSection('account')}
                    >
                      <User size={18} />
                      Account
                    </button>
                  </div>

                  <div className="settings-content">
                    {settingsSection === 'general' && (
                      <div className="settings-list">
                        <div className="settings-row">
                          <span>Appearance</span>
                          <div className="settings-dropdown">
                            <button
                              type="button"
                              className="settings-dropdown__trigger-compact"
                              onClick={() => setIsThemeDropdownOpen(!isThemeDropdownOpen)}
                            >
                              <span>{theme === 'dark' ? 'Dark' : 'Light'}</span>
                              <ChevronDown size={16} className={isThemeDropdownOpen ? 'rotate-180' : ''} />
                            </button>
                            {isThemeDropdownOpen && (
                              <div className="settings-dropdown__panel">
                                <button
                                  type="button"
                                  className={`settings-dropdown__option ${theme === 'dark' ? 'is-active' : ''}`}
                                  onClick={() => {
                                    setTheme('dark');
                                    setIsThemeDropdownOpen(false);
                                  }}
                                >
                                  <span>Dark</span>
                                  {theme === 'dark' && <Check size={16} />}
                                </button>
                                <button
                                  type="button"
                                  className={`settings-dropdown__option ${theme === 'light' ? 'is-active' : ''}`}
                                  onClick={() => {
                                    setTheme('light');
                                    setIsThemeDropdownOpen(false);
                                  }}
                                >
                                  <span>Light</span>
                                  {theme === 'light' && <Check size={16} />}
                                </button>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    )}

                    {settingsSection === 'data-controls' && (
                      <div className="settings-list">
                        <div className="settings-row">
                          <span>Improve model for everyone</span>
                          <button type="button" className="locked-toggle is-on" aria-label="Enabled" disabled>
                            <span />
                          </button>
                        </div>
                        <div className="settings-row">
                          <span>Archive all chats</span>
                          <button type="button" className="settings-inline-btn" onClick={handleArchiveAllChats}>
                            Archive
                          </button>
                        </div>
                        <div className="settings-row">
                          <span>Delete all chats</span>
                          <button type="button" className="settings-inline-btn is-danger" onClick={handleDeleteAllChats}>
                            Delete
                          </button>
                        </div>
                      </div>
                    )}

                    {settingsSection === 'security' && (
                      <div className="settings-list">
                        {securityMode === 'overview' ? (
                          <button
                            type="button"
                            className="settings-row security-row"
                            onClick={() => {
                              setSecurityMode('change-password');
                              setProfileNotice('');
                            }}
                          >
                            <span>Password</span>
                            <div className="account-row__value">
                              <strong>******</strong>
                              <span>&rsaquo;</span>
                            </div>
                          </button>
                        ) : (
                          <div className="security-form-wrap">
                            <form className="security-form" onSubmit={handlePasswordSave}>
                              <label className="profile-editor-field">
                                <span>Current password</span>
                                <input
                                  className="form-input"
                                  type="password"
                                  value={passwordDraft.current}
                                  onChange={(event) =>
                                    setPasswordDraft((prev) => ({ ...prev, current: event.target.value }))
                                  }
                                />
                              </label>
                              <label className="profile-editor-field">
                                <span>New password</span>
                                <input
                                  className="form-input"
                                  type="password"
                                  value={passwordDraft.next}
                                  onChange={(event) =>
                                    setPasswordDraft((prev) => ({ ...prev, next: event.target.value }))
                                  }
                                />
                              </label>
                              <label className="profile-editor-field">
                                <span>Confirm new password</span>
                                <input
                                  className="form-input"
                                  type="password"
                                  value={passwordDraft.confirm}
                                  onChange={(event) =>
                                    setPasswordDraft((prev) => ({ ...prev, confirm: event.target.value }))
                                  }
                                />
                              </label>
                              <div className="security-form__actions">
                                <button
                                  type="button"
                                  className="screening-form__back"
                                  onClick={() => setSecurityMode('overview')}
                                >
                                  Cancel
                                </button>
                                <button type="submit" className="btn-primary profile-save-btn">
                                  Update password
                                </button>
                              </div>
                            </form>
                          </div>
                        )}
                      </div>
                    )}

                    {settingsSection === 'account' && (
                      <div className="settings-list">
                        <div className="settings-row">
                          <span>Name</span>
                          <strong>{profileDraft.displayName || displayName}</strong>
                        </div>
                        <div className="settings-row">
                          <span>Email</span>
                          <div className="account-row__value">
                            <strong>{user?.email ?? 'Unknown'}</strong>
                            <span>&rsaquo;</span>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </section>
              )}

              {profileView === 'personalization' && (
                <section className="personalization-container">
                  <div className="personalization-hero">
                    <SlidersHorizontal size={42} className="text-accent mb-4" />
                    <h3>Tailor your experience</h3>
                    <p>Review your intake questions and assessments separately, and revise only what you want.</p>
                  </div>

                  <div className="profile-grid">
                    <div className="personalization-card">
                      <div className="personalization-card__header">
                        <Brain size={20} />
                        <span>Clinical Intake</span>
                      </div>
                      <div className="personalization-card__body">
                        <p>Update your initial questions and context if your situation has changed.</p>
                        <button
                          type="button"
                          className="personalization-card__action"
                          onClick={handleReviseIntake}
                        >
                          Revise intake
                        </button>
                      </div>
                    </div>

                    <div className="personalization-card">
                      <div className="personalization-card__header">
                        <ClipboardList size={20} />
                        <span>Assessments</span>
                      </div>
                      <div className="personalization-card__body">
                        <p>Revisit PHQ-9 and GAD-7 separately from the intake questions.</p>
                        <button
                          type="button"
                          className="personalization-card__action"
                          onClick={handleReviseAssessments}
                        >
                          Revise tests
                        </button>
                      </div>
                    </div>

                    <div className="personalization-card">
                      <div className="personalization-card__header">
                        <Sparkles size={20} />
                        <span>Mood tracker</span>
                      </div>
                      <div className="personalization-card__body">
                        <p>{moodTrend?.summary || 'Log quick mood signals so the assistant can adapt over time.'}</p>
                        <div className="profile-editor-fields">
                          <label className="profile-editor-field">
                            <span>Mood (1-10)</span>
                            <input
                              className="form-input"
                              type="number"
                              min="1"
                              max="10"
                              value={moodDraft.mood_score}
                              onChange={(event) => setMoodDraft((prev) => ({ ...prev, mood_score: Number(event.target.value) }))}
                            />
                          </label>
                          <label className="profile-editor-field">
                            <span>Anxiety (1-10)</span>
                            <input
                              className="form-input"
                              type="number"
                              min="1"
                              max="10"
                              value={moodDraft.anxiety_score}
                              onChange={(event) => setMoodDraft((prev) => ({ ...prev, anxiety_score: Number(event.target.value) }))}
                            />
                          </label>
                          <label className="profile-editor-field">
                            <span>Sleep quality (1-10)</span>
                            <input
                              className="form-input"
                              type="number"
                              min="1"
                              max="10"
                              value={moodDraft.sleep_quality}
                              onChange={(event) => setMoodDraft((prev) => ({ ...prev, sleep_quality: Number(event.target.value) }))}
                            />
                          </label>
                          <label className="profile-editor-field">
                            <span>Notes</span>
                            <input
                              className="form-input"
                              value={moodDraft.notes}
                              onChange={(event) => setMoodDraft((prev) => ({ ...prev, notes: event.target.value }))}
                            />
                          </label>
                        </div>
                        <button type="button" className="personalization-card__action" onClick={handleMoodSave}>
                          Save mood check-in
                        </button>
                      </div>
                    </div>

                    <div className="personalization-card">
                      <div className="personalization-card__header">
                        <FileText size={20} />
                        <span>Private journal</span>
                      </div>
                      <div className="personalization-card__body">
                        <p>{journalInsights?.summary || 'Write short reflections and optionally let Calma use them in future replies.'}</p>
                        <div className="profile-editor-fields">
                          <label className="profile-editor-field">
                            <span>Title</span>
                            <input
                              className="form-input"
                              value={journalDraft.title}
                              onChange={(event) => setJournalDraft((prev) => ({ ...prev, title: event.target.value }))}
                            />
                          </label>
                          <label className="profile-editor-field">
                            <span>Entry</span>
                            <textarea
                              className="form-input"
                              rows="4"
                              value={journalDraft.content}
                              onChange={(event) => setJournalDraft((prev) => ({ ...prev, content: event.target.value }))}
                            />
                          </label>
                          <label className="profile-editor-field">
                            <span className="flex items-center justify-between">
                              <span>Allow chat to use this entry</span>
                              <input
                                type="checkbox"
                                checked={journalDraft.consent_for_chat}
                                onChange={(event) => setJournalDraft((prev) => ({ ...prev, consent_for_chat: event.target.checked }))}
                              />
                            </span>
                          </label>
                        </div>
                        <button type="button" className="personalization-card__action" onClick={handleJournalSave}>
                          Save journal entry
                        </button>
                      </div>
                    </div>
                  </div>
                </section>
              )}

              {profileView === 'help' && (
                <section className="profile-menu-sections">
                  <button type="button" className="profile-menu-section">
                    <CircleHelp size={18} />
                    Help Center
                  </button>
                  <button type="button" className="profile-menu-section">
                    <FileText size={18} />
                    Terms of Service
                  </button>
                  <button type="button" className="profile-menu-section">
                    <Shield size={18} />
                    Privacy Policy
                  </button>
                  <button type="button" className="profile-menu-section">
                    <ExternalLink size={18} />
                    Report a bug
                  </button>
                </section>
              )}

              {profileNotice && <div className="screening-inline-error profile-notice">{profileNotice}</div>}

              <div className="profile-panel__actions">
                {profileView === 'profile' && (
                  <>
                    <button type="button" className="screening-form__back" onClick={() => setIsProfileOpen(false)}>
                      Cancel
                    </button>
                    <button type="submit" className="btn-primary profile-save-btn">
                      Save
                    </button>
                  </>
                )}
              </div>
            </form>
          </div>
        </div>
      )}

      {openSessionMenuId && (
        <div
          ref={sessionMenuRef}
          className="history-item__menu"
          style={{ position: 'fixed', top: menuPosition.top, left: menuPosition.left, transform: 'none' }}
          onClick={(event) => event.stopPropagation()}
        >
          <button
            type="button"
            className="history-item__menu-item"
            onClick={() => handleSessionArchive(openSessionMenuId)}
            disabled={sessionActionBusyId === openSessionMenuId}
          >
            <Archive size={22} />
            <span>Arşivle</span>
          </button>
          <button
            type="button"
            className="history-item__menu-item is-danger"
            onClick={() => handleSessionDelete(openSessionMenuId)}
            disabled={sessionActionBusyId === openSessionMenuId}
          >
            <Trash2 size={22} />
            <span>Sil</span>
          </button>
        </div>
      )}
    </div>
  );
}

export default App;
