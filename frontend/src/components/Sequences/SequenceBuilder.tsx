import React, { useState, useEffect, useMemo } from 'react';
import {
  PlusIcon,
  TrashIcon,
  PlayIcon,
  PauseIcon,
  ArrowPathIcon,
  ChevronDownIcon,
  ChevronRightIcon,
  GlobeAltIcon,
} from '@heroicons/react/24/outline';
import { apiService } from '../../services/api';
import toast from 'react-hot-toast';

interface IntegrationStep {
  id?: number;
  name: string;
  integration_type: string;
  api_endpoint: string;
  http_method: string;
  sequence_order: number;
  auth_type: string;
  auth_config: any;
  depends_on_fields: Record<string, string>;
  output_fields: string[];
  is_active: boolean;
  timeout_seconds?: number;
  retry_count?: number;
  retry_delay_seconds?: number;
  rate_limit_per_minute?: number;
  request_headers?: Record<string, string>;
  request_schema?: { template?: any } | any;
}

interface IntegrationSequence {
  id?: number;
  name: string;
  description: string;
  sequence_type: string;
  execution_mode: string;
  condition_config: any;
  stop_on_error: boolean;
  retry_failed_steps: boolean;
  is_active: boolean;
  steps: IntegrationStep[];
}

interface SequenceBuilderProps {
  lenderId: number;
  onSequenceChange: (sequence: IntegrationSequence) => void;
  initialSequence?: IntegrationSequence;
  onValidityChange?: (isValid: boolean) => void;
}

const SequenceBuilder: React.FC<SequenceBuilderProps> = ({
  lenderId,
  onSequenceChange,
  initialSequence,
  onValidityChange
}) => {
  const [sequence, setSequence] = useState<IntegrationSequence>(
    initialSequence || {
      name: 'New Integration Sequence',
      description: 'Configure your API integration steps',
      sequence_type: 'LEAD_SUBMISSION',
      execution_mode: 'sequential',
      condition_config: {},
      stop_on_error: true,
      retry_failed_steps: false,
      is_active: true,
      steps: [{
        name: 'Step 1',
        integration_type: 'LEAD_SUBMISSION',
        api_endpoint: '',
        http_method: 'POST',
        sequence_order: 1,
        auth_type: 'NONE',
        auth_config: {},
        depends_on_fields: {},
        output_fields: [],
        is_active: true
      }]
    }
  );
  const [expandedSteps, setExpandedSteps] = useState<Set<number>>(new Set());
  const [isValid, setIsValid] = useState(false);
  const [templateText, setTemplateText] = useState<Record<number, string>>({});
  const [templateError, setTemplateError] = useState<Record<number, string | undefined>>({});
  const [dnsValidationStatus, setDnsValidationStatus] = useState<Record<number, { loading: boolean; valid: boolean; message: string }>>({});

  const allowedHttpMethods = useMemo(() => new Set(['GET','POST','PUT','PATCH','DELETE']), []);

  const isValidEndpoint = (value: string): boolean => {
    if (!value) return false;
    return /^https?:\/\//.test(value) || value.startsWith('/');
  };

  const isValidJsonPath = (value: string): boolean => {
    if (!value) return true; // allow empty
    return value.startsWith('$.');
  };

  const validateDns = async (url: string, stepIndex: number): Promise<void> => {
    if (!url || !url.startsWith('http')) {
      setDnsValidationStatus(prev => ({
        ...prev,
        [stepIndex]: { loading: false, valid: false, message: 'URL must start with http:// or https://' }
      }));
      return;
    }

    try {
      const urlObj = new URL(url);
      const hostname = urlObj.hostname;
      
      // Basic hostname validation
      if (!hostname || hostname.length === 0) {
        setDnsValidationStatus(prev => ({
          ...prev,
          [stepIndex]: { loading: false, valid: false, message: 'Invalid hostname in URL' }
        }));
        return;
      }

      setDnsValidationStatus(prev => ({
        ...prev,
        [stepIndex]: { loading: true, valid: false, message: `Checking DNS resolution for ${hostname}...` }
      }));

      // Create a simple DNS resolution check using fetch
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout
      
      try {
        const response = await fetch(url, {
          method: 'HEAD',
          mode: 'no-cors',
          signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        setDnsValidationStatus(prev => ({
          ...prev,
          [stepIndex]: { loading: false, valid: true, message: `DNS resolution successful for ${hostname}` }
        }));
        
        toast.success(`DNS validation successful for ${hostname}`);
      } catch (fetchError) {
        clearTimeout(timeoutId);
        
        // Even if fetch fails, we can still check if the hostname resolves
        // This handles cases where the endpoint exists but returns an error
        setDnsValidationStatus(prev => ({
          ...prev,
          [stepIndex]: { loading: false, valid: true, message: `Hostname ${hostname} is reachable (endpoint may have restrictions)` }
        }));
        
        toast.success(`DNS validation successful for ${hostname}`);
      }
    } catch (error) {
      let message = 'DNS resolution failed';
      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          message = 'DNS resolution timeout';
        } else if (error.message.includes('Failed to fetch')) {
          message = 'DNS resolution failed - host not reachable';
        } else if (error.message.includes('Invalid URL')) {
          message = 'Invalid URL format';
        } else {
          message = `DNS resolution error: ${error.message}`;
        }
      }
      
      setDnsValidationStatus(prev => ({
        ...prev,
        [stepIndex]: { loading: false, valid: false, message }
      }));
      
      toast.error(`DNS validation failed: ${message}`);
    }
  };

  const validateSequence = (seq: IntegrationSequence): boolean => {
    // Basic validation - only check essential fields
    if (!seq.name || !seq.name.trim()) return false;
    if (!seq.steps || seq.steps.length === 0) return false;
    
    // Check if at least one step has basic required fields
    let hasValidStep = false;
    for (let i = 0; i < seq.steps.length; i++) {
      const step = seq.steps[i];
      if (step.name && step.name.trim() && step.api_endpoint && step.api_endpoint.trim()) {
        hasValidStep = true;
        break;
      }
    }
    
    if (!hasValidStep) return false;
    
    // More lenient validation - don't fail on optional fields
    for (let i = 0; i < seq.steps.length; i++) {
      const step = seq.steps[i];
      
      // Only validate if step has content
      if (step.name && step.name.trim() && step.api_endpoint && step.api_endpoint.trim()) {
        if (!allowedHttpMethods.has(step.http_method)) return false;
        if (!isValidEndpoint(step.api_endpoint)) return false;
        
        // Validate output fields only if they exist and have content
        for (const out of step.output_fields || []) {
          if (out && out.trim() && !isValidJsonPath(out)) return false;
        }
        
        // Validate template JSON only if it exists and has content
        const t = templateText[i];
        if (typeof t === 'string' && t.trim()) {
          try { 
            JSON.parse(t); 
          } catch { 
            return false; 
          }
        }
      }
    }
    return true;
  };

  useEffect(() => {
    onSequenceChange(sequence);
    const ok = validateSequence(sequence);
    setIsValid(ok);
    if (onValidityChange) onValidityChange(ok);
    
    // Debug logging for validation
    console.log('Sequence validation:', {
      isValid: ok,
      sequenceName: sequence.name,
      stepsCount: sequence.steps.length,
      steps: sequence.steps.map(step => ({
        name: step.name,
        api_endpoint: step.api_endpoint,
        hasName: !!step.name?.trim(),
        hasEndpoint: !!step.api_endpoint?.trim()
      }))
    });
    
    // Clear DNS validation statuses when sequence changes
    setDnsValidationStatus({});
  }, [sequence, onSequenceChange, onValidityChange]);

  // Update sequence when initialSequence prop changes
  useEffect(() => {
    console.log('SequenceBuilder: initialSequence prop changed:', initialSequence);
    if (initialSequence) {
      console.log('SequenceBuilder: Updating sequence from initialSequence prop:', initialSequence);
      setSequence(initialSequence);
      setDnsValidationStatus({});
    }
  }, [initialSequence]);

  // Debug: Log current sequence state
  useEffect(() => {
    console.log('SequenceBuilder: Current sequence state:', sequence);
  }, [sequence]);

  const addStep = () => {
    const newStep: IntegrationStep = {
      name: `Step ${sequence.steps.length + 1}`,
      integration_type: 'LEAD_SUBMISSION',
      api_endpoint: '',
      http_method: 'POST',
      sequence_order: sequence.steps.length + 1,
      auth_type: 'NONE',
      auth_config: {},
      depends_on_fields: {},
      output_fields: [],
      is_active: true
    };
    setSequence({
      ...sequence,
      steps: [...sequence.steps, newStep]
    });
    
    // Clear DNS validation status for new step
    const newIndex = sequence.steps.length;
    setDnsValidationStatus(prev => {
      const newStatus = { ...prev };
      delete newStatus[newIndex];
      return newStatus;
    });
  };

  const updateStep = (index: number, field: keyof IntegrationStep, value: any) => {
    const updatedSteps = [...sequence.steps];
    updatedSteps[index] = { ...updatedSteps[index], [field]: value };
    setSequence({ ...sequence, steps: updatedSteps });
    
    // Clear DNS validation status when API endpoint changes
    if (field === 'api_endpoint') {
      setDnsValidationStatus(prev => {
        const newStatus = { ...prev };
        delete newStatus[index];
        return newStatus;
      });
    }
  };

  const updateAuthConfig = (index: number, updates: Record<string, any>) => {
    const step = sequence.steps[index];
    const next = { ...(step.auth_config || {}), ...updates };
    updateStep(index, 'auth_config', next);
  };

  const removeStep = (index: number) => {
    const proceed = window.confirm('Remove this step? This cannot be undone.');
    if (!proceed) return;
    
    // Don't allow removing the last step
    if (sequence.steps.length <= 1) {
      toast.error('Cannot remove the last step. At least one step is required.');
      return;
    }
    
    const updatedSteps = sequence.steps.filter((_, i) => i !== index);
    // Reorder remaining steps
    updatedSteps.forEach((step, i) => {
      step.sequence_order = i + 1;
    });
    setSequence({ ...sequence, steps: updatedSteps });
    
    // Clear DNS validation status for removed step
    setDnsValidationStatus(prev => {
      const newStatus = { ...prev };
      delete newStatus[index];
      return newStatus;
    });
  };

  const duplicateStep = (index: number) => {
    const target = sequence.steps[index];
    const clone: IntegrationStep = { ...target, id: undefined, name: `${target.name} (copy)`, sequence_order: sequence.steps.length + 1 };
    setSequence({ ...sequence, steps: [...sequence.steps, clone] });
    
    // Clear DNS validation status for duplicated step (it will be re-validated if needed)
    const newIndex = sequence.steps.length;
    setDnsValidationStatus(prev => {
      const newStatus = { ...prev };
      delete newStatus[newIndex];
      return newStatus;
    });
  };

  // cURL modal state
  const [showCurlModal, setShowCurlModal] = useState(false);
  const [curlText, setCurlText] = useState('');
  const [curlTargetIndex, setCurlTargetIndex] = useState<number | null>(null);

  const parseCurl = (text: string) => {
    try {
      // Normalize: join backslash-newlines, convert fancy dashes to --
      const unified = text
        .replace(/\\\s*\n/g, ' ')
        .replace(/[\u2012\u2013\u2014\u2015\u2212]/g, '--')
        .replace(/[\u2018\u2019]/g, "'")
        .replace(/[\u201C\u201D]/g, '"');
      const lines = unified.split(/[\r\n]+/).join(' ').trim();
      // Prefer --url, fallback to first http(s) occurrence or leading path
      const urlFromFlag = (() => {
        const m = lines.match(/--url\s+(?:'([^']+)'|\"([^\"]+)\"|([^\s]+))/i);
        if (!m) return '';
        return m[1] || m[2] || m[3] || '';
      })();
      const quotedUrlFirst = (() => {
        const m = lines.match(/['\"]((?:https?:\/\/|\/)[^'\"]+)['\"]/);
        return m ? (m[1] || '') : '';
      })();
      // Try to choose endpoint URL, avoiding URLs inside headers like User-Agent
      let urlMatch = '';
      if (urlFromFlag) {
        urlMatch = urlFromFlag;
      } else if (quotedUrlFirst) {
        urlMatch = quotedUrlFirst;
      } else {
        const urls: { url: string; index: number }[] = [];
        const re = /https?:\/\/[^\s'\"]+/g;
        let m: RegExpExecArray | null;
        while ((m = re.exec(lines)) !== null) {
          urls.push({ url: m[0], index: m.index });
        }
        const headerPos = (() => {
          const mH = lines.match(/(?:\s|^)(?:-H|--header)\b/);
          return mH ? mH.index ?? Number.MAX_SAFE_INTEGER : Number.MAX_SAFE_INTEGER;
        })();
        const candidates = urls.filter(u => u.index < headerPos + 5);
        const chosen = (candidates.length > 0 ? candidates : urls)
          .sort((a, b) => b.url.length - a.url.length)[0];
        urlMatch = chosen ? chosen.url : '';
      }
      if (!urlMatch) {
        // Try to find a quoted or unquoted path starting with /
        const mPath = lines.match(/\s'(\/[A-Za-z0-9._~:\/?#\[\]@!$&'()*+,;=%-]+)'/) ||
                      lines.match(/\s\"(\/[A-Za-z0-9._~:\/?#\[\]@!$&'()*+,;=%-]+)\"/) ||
                      lines.match(/\s(\/[A-Za-z0-9._~:\/?#\[\]@!$&'()*+,;=%-]+)/);
        urlMatch = (mPath && (mPath[1] || mPath[2] || mPath[3])) || '';
      }
      const methodMatch =
        lines.match(/(?:--|—|–)?request\s+(GET|POST|PUT|PATCH|DELETE)/i) ||
        lines.match(/-X\s+(GET|POST|PUT|PATCH|DELETE)/i);
      const hasGetWithData = /\s-G(\s|$)/.test(lines);
      // Headers: support -H and --header with single or double quotes
      const headerMatches = [
        ...lines.matchAll(/(?:-H|--header)\s+'([^']+)'/g),
        ...lines.matchAll(/(?:-H|--header)\s+\"([^\"]+)\"/g),
        ...lines.matchAll(/(?:-H|--header)\s+\$'([^']+)'/g),
        ...lines.matchAll(/(?:-H|--header)\s+([^\s][^\s]*)/g),
      ];
      const dataRawMatch =
        lines.match(/--data-raw\s+'([^']+)'/) ||
        lines.match(/--data-raw\s+\"([^\"]+)\"/) ||
        lines.match(/--data-raw\s+\$'([^']+)'/);
      const dataMatch =
        lines.match(/--data\s+'([^']+)'/) ||
        lines.match(/--data\s+\"([^\"]+)\"/) ||
        lines.match(/-d\s+'([^']+)'/) ||
        lines.match(/-d\s+\"([^\"]+)\"/) ||
        lines.match(/--data-binary\s+'([^']+)'/) ||
        lines.match(/--data-binary\s+\"([^\"]+)\"/) ||
        lines.match(/--data-urlencode\s+'([^']+)'/) ||
        lines.match(/--data-urlencode\s+\"([^\"]+)\"/);

      const fullUrl = urlMatch || '';
      let method = methodMatch ? methodMatch[1].toUpperCase() : ((dataRawMatch || dataMatch) ? 'POST' : 'GET');
      if (hasGetWithData) method = 'GET';

      const headers: Record<string, string> = {};
      for (const m of headerMatches) {
        const hv = (m[1] || '').trim();
        const idx = hv.indexOf(':');
        if (idx > -1) {
          const k = hv.slice(0, idx).trim();
          const v = hv.slice(idx + 1).trim();
          if (k) headers[k] = v;
        }
      }

      const bodyStr = (dataRawMatch && dataRawMatch[1]) || (dataMatch && dataMatch[1]) || '';
      let body: any = undefined;
      let params: Record<string, string> = {};

      // Parse URL query params
      try {
        if (fullUrl) {
          const baseForPath = fullUrl.startsWith('/') ? 'http://local' : undefined;
          const u = baseForPath ? new URL(fullUrl, baseForPath) : new URL(fullUrl);
          u.searchParams.forEach((v, k) => {
            params[k] = v;
          });
        }
      } catch {}

      // Parse body as JSON or form-encoded
      if (bodyStr) {
        const isJsonLike = bodyStr.trim().startsWith('{') || bodyStr.trim().startsWith('[');
        if (isJsonLike) {
          try { body = JSON.parse(bodyStr); } catch { body = undefined; }
        } else {
          // form urlencoded a=1&b=2
          const formParams: Record<string, string> = {};
          bodyStr.split('&').forEach((pair) => {
            const [k, v] = pair.split('=');
            if (k) formParams[decodeURIComponent(k)] = decodeURIComponent(v || '');
          });
          if (hasGetWithData || method === 'GET') {
            params = { ...params, ...formParams };
          } else {
            body = formParams;
          }
        }
      }

      return { url: fullUrl, method, headers, body, params };
    } catch {
      return { url: '', method: 'POST', headers: {}, body: undefined, params: {} };
    }
  };

  const applyCurlToStep = async (index: number) => {
    let parsed: { url: string; method: string; headers: Record<string, string>; body: any; params: Record<string, string> } | null = null;
    try {
      const resp = await apiService.post<any>(`/utils/parse-curl`, { curl: curlText });
      console.log('Parse curl response:', resp);
      
      if ((resp as any)?.data || (resp as any)?.url) {
        const d: any = (resp as any).data || resp;
        parsed = {
          url: d.url || '',
          method: (d.method || '').toUpperCase(),
          headers: d.headers || {},
          body: d.body,
          params: d.params || {}
        };
        console.log('Parsed curl data:', parsed);
      }
    } catch (error) {
      console.error('Error parsing curl:', error);
      toast.error('Failed to parse cURL command');
      return;
    }

    if (!parsed) {
      toast.error('Failed to parse cURL command');
      return;
    }

    // Use server response only (no client regex) as requested
    const url = (parsed.url || '').trim();
    const method = (parsed.method || '').toUpperCase();
    const headers = parsed.headers || {} as Record<string, string>;
    const body = parsed.body as any;
    const params = parsed.params || {} as Record<string, string>;
    
    console.log('Applying to step:', { url, method, headers, body, params });
    
    // Get current step and prepare all updates
    const currentStep = sequence.steps[index];
    const updatedStep = { ...currentStep };
    
    // Update basic fields
    if (url) {
      updatedStep.api_endpoint = url;
      console.log('Updated API endpoint:', url);
    }
    
    if (method) {
      updatedStep.http_method = method;
      console.log('Updated HTTP method:', method);
    }
    
    if (headers && Object.keys(headers).length > 0) {
      updatedStep.request_headers = headers;
      console.log('Updated request headers:', headers);
      
      // Handle authentication headers
      const authHeader = Object.keys(headers).find(k => k.toLowerCase() === 'authorization');
      if (authHeader) {
        const val = headers[authHeader];
        const m = /bearer\s+(.+)/i.exec(val || '');
        if (m && m[1]) {
          updatedStep.auth_type = 'BEARER_TOKEN' as any;
          updatedStep.auth_config = { ...(updatedStep.auth_config || {}), token: m[1].trim() };
          console.log('Updated auth type to BEARER_TOKEN');
        }
      } else {
        const apiKeyHeader = Object.keys(headers).find(k => /api[-_ ]?key|x-api-key/i.test(k));
        if (apiKeyHeader) {
          updatedStep.auth_type = 'API_KEY' as any;
          updatedStep.auth_config = { ...(updatedStep.auth_config || {}), key_name: apiKeyHeader, key_value: headers[apiKeyHeader], key_location: 'header' };
          console.log('Updated auth type to API_KEY');
        }
      }
    }
    
    // Update request schema
    if (body || (params && Object.keys(params).length > 0)) {
      const schema = { ...(updatedStep.request_schema || {}) } as any;
      
      if (body) {
        schema.template = body;
        try { 
          setTemplateText(prev => ({ ...prev, [index]: JSON.stringify(body, null, 2) })); 
          console.log('Updated request schema template');
        } catch (e) {
          console.error('Error setting template text:', e);
        }
      }
      
      if (params && Object.keys(params).length > 0) {
        schema.query_params = { ...(schema.query_params || {}), ...params };
        console.log('Updated query params:', params);
      }
      
      updatedStep.request_schema = schema;
      console.log('Updated request schema:', schema);
    }
    
    // Apply all updates at once
    const updatedSteps = [...sequence.steps];
    updatedSteps[index] = updatedStep;
    setSequence({ ...sequence, steps: updatedSteps });
    
    console.log('Applied all updates to step:', updatedStep);
    
    // Force the step to expand so user can see the populated fields
    setExpandedSteps(prev => new Set([...prev, index]));
    
    setShowCurlModal(false);
    setCurlText('');
    setCurlTargetIndex(null);
    
    toast.success('cURL applied successfully!');
  };

  // Suggest outputs from latest run
  const suggestOutputsFromLastRun = async (index: number) => {
    try {
      const runs = await apiService.get<{ run_id: string; last_at: string }[]>(`/lenders/${lenderId}/runs`);
      const latest = runs.data?.[0]?.run_id;
      if (!latest) return;
      const logs = await apiService.get<any[]>(`/lenders/${lenderId}/runs/${latest}`);
      const resp = logs.data?.find((l: any) => l.step_order === sequence.steps[index].sequence_order)?.response_data;
      if (!resp || typeof resp !== 'object') return;
      const keys = Object.keys(resp);
      const jsonpaths = keys.slice(0, 5).map(k => `$.${k}`);
      updateStep(index, 'output_fields', Array.from(new Set([...(sequence.steps[index].output_fields || []), ...jsonpaths])));
    } catch (e) {
      // no-op
    }
  };

  // Headers helpers
  const addHeader = (stepIndex: number) => {
    const step = sequence.steps[stepIndex];
    const headers = { ...(step.request_headers || {}) };
    let newKey = 'X-Header';
    let suffix = 1;
    while (headers[newKey]) { newKey = `X-Header-${suffix++}`; }
    headers[newKey] = '';
    updateStep(stepIndex, 'request_headers', headers);
  };

  const updateHeader = (stepIndex: number, oldKey: string, newKey: string, value: string) => {
    const step = sequence.steps[stepIndex];
    const headers = { ...(step.request_headers || {}) };
    delete headers[oldKey];
    headers[newKey] = value;
    updateStep(stepIndex, 'request_headers', headers);
  };

  const removeHeader = (stepIndex: number, key: string) => {
    const step = sequence.steps[stepIndex];
    const headers = { ...(step.request_headers || {}) };
    delete headers[key];
    updateStep(stepIndex, 'request_headers', headers);
  };

  // Template helpers
  const handleTemplateChange = (stepIndex: number, text: string) => {
    setTemplateText(prev => ({ ...prev, [stepIndex]: text }));
    if (!text.trim()) {
      // empty template clears
      const step = sequence.steps[stepIndex];
      const schema = { ...(step.request_schema || {}) };
      delete schema.template;
      updateStep(stepIndex, 'request_schema', schema);
      setTemplateError(prev => ({ ...prev, [stepIndex]: undefined }));
      return;
    }
    try {
      const parsed = JSON.parse(text);
      const step = sequence.steps[stepIndex];
      const schema = { ...(step.request_schema || {}) };
      schema.template = parsed;
      updateStep(stepIndex, 'request_schema', schema);
      setTemplateError(prev => ({ ...prev, [stepIndex]: undefined }));
    } catch (e: any) {
      setTemplateError(prev => ({ ...prev, [stepIndex]: 'Invalid JSON' }));
    }
  };

  const toggleStepExpanded = (index: number) => {
    const newExpanded = new Set(expandedSteps);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedSteps(newExpanded);
  };

  const addDependency = (stepIndex: number) => {
    const step = sequence.steps[stepIndex];
    const newDependsOn = { ...step.depends_on_fields, '': '' };
    updateStep(stepIndex, 'depends_on_fields', newDependsOn);
  };

  const updateDependency = (stepIndex: number, oldKey: string, newKey: string, value: string) => {
    const step = sequence.steps[stepIndex];
    const newDependsOn = { ...step.depends_on_fields };
    delete newDependsOn[oldKey];
    newDependsOn[newKey] = value;
    updateStep(stepIndex, 'depends_on_fields', newDependsOn);
  };

  const removeDependency = (stepIndex: number, key: string) => {
    const step = sequence.steps[stepIndex];
    const newDependsOn = { ...step.depends_on_fields };
    delete newDependsOn[key];
    updateStep(stepIndex, 'depends_on_fields', newDependsOn);
  };

  const addOutputField = (stepIndex: number) => {
    const step = sequence.steps[stepIndex];
    const newOutputFields = [...step.output_fields, ''];
    updateStep(stepIndex, 'output_fields', newOutputFields);
  };

  const updateOutputField = (stepIndex: number, fieldIndex: number, value: string) => {
    const step = sequence.steps[stepIndex];
    const newOutputFields = [...step.output_fields];
    newOutputFields[fieldIndex] = value;
    updateStep(stepIndex, 'output_fields', newOutputFields);
  };

  const removeOutputField = (stepIndex: number, fieldIndex: number) => {
    const step = sequence.steps[stepIndex];
    const newOutputFields = step.output_fields.filter((_, i) => i !== fieldIndex);
    updateStep(stepIndex, 'output_fields', newOutputFields);
  };

  const testSequence = async () => {
    try {
      const testData = {
        full_name: 'John Doe',
        email: 'john@example.com',
        phone: '+1-555-123-4567',
        loan_amount: '50000'
      };

      const response = await apiService.post(`/lenders/${lenderId}/test-integration`, {
        sequence_id: sequence.id,
        test_data: testData
      });

      toast.success('Sequence test completed successfully!');
      console.log('Test result:', response.data);
    } catch (error) {
      toast.error('Sequence test failed');
      console.error('Test error:', error);
    }
  };

  const getExecutionModeOptions = () => [
    { value: 'sequential', label: 'Sequential (one after another)' },
    { value: 'parallel', label: 'Parallel (all at once)' },
    { value: 'conditional', label: 'Conditional (based on conditions)' }
  ];

  const getIntegrationTypeOptions = () => [
    { value: 'LEAD_SUBMISSION', label: 'Lead Submission' },
    { value: 'STATUS_CHECK', label: 'Status Check' },
    { value: 'BULK_UPLOAD', label: 'Bulk Upload' },
    { value: 'WEBHOOK', label: 'Webhook' },
    { value: 'POLLING', label: 'Polling' }
  ];

  const getHttpMethodOptions = () => [
    { value: 'GET', label: 'GET' },
    { value: 'POST', label: 'POST' },
    { value: 'PUT', label: 'PUT' },
    { value: 'PATCH', label: 'PATCH' },
    { value: 'DELETE', label: 'DELETE' }
  ];

  const getAuthTypeOptions = () => [
    { value: 'NONE', label: 'None' },
    { value: 'API_KEY', label: 'API Key' },
    { value: 'BEARER_TOKEN', label: 'Bearer Token' },
    { value: 'BASIC_AUTH', label: 'Basic Auth' },
    { value: 'OAUTH2', label: 'OAuth2' }
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-medium text-gray-900">Integration Sequence</h3>
          <p className="text-sm text-gray-500">
            Configure multi-step API integration sequence
          </p>
        </div>
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full ${isValid ? 'bg-green-500' : 'bg-red-500'}`}></div>
            <span className={`text-sm ${isValid ? 'text-green-700' : 'text-red-700'}`}>
              {isValid ? 'Sequence is valid' : 'Sequence needs configuration'}
            </span>
          </div>
          <div className="flex space-x-2">
            {process.env.NODE_ENV === 'development' && (
              <button
                onClick={() => {
                  console.log('Current validation state:', {
                    isValid,
                    sequence,
                    validationResult: validateSequence(sequence)
                  });
                }}
                className="px-3 py-2 text-sm font-medium text-gray-600 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200"
              >
                Debug Validation
              </button>
            )}
            <button
              onClick={testSequence}
              disabled={!isValid}
              className={`flex items-center space-x-1 px-3 py-2 text-sm font-medium text-white border border-transparent rounded-md ${isValid ? 'bg-green-600 hover:bg-green-700' : 'bg-gray-400 cursor-not-allowed'}`}
            >
              <PlayIcon className="w-4 h-4" />
              <span>Test Sequence</span>
            </button>
          </div>
        </div>
      </div>

      {/* Sequence Configuration */}
      <div className="bg-white p-6 rounded-lg border border-gray-200">
        <h4 className="text-md font-medium text-gray-900 mb-4">Sequence Configuration</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Sequence Name</label>
            <input
              type="text"
              value={sequence.name}
              onChange={(e) => setSequence({ ...sequence, name: e.target.value })}
              placeholder="Enter sequence name"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              onFocus={(e) => e.target.select()}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Sequence Type</label>
            <select
              value={sequence.sequence_type}
              onChange={(e) => setSequence({ ...sequence, sequence_type: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {getIntegrationTypeOptions().map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Execution Mode</label>
            <select
              value={sequence.execution_mode}
              onChange={(e) => setSequence({ ...sequence, execution_mode: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {getExecutionModeOptions().map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <input
              type="text"
              value={sequence.description}
              onChange={(e) => setSequence({ ...sequence, description: e.target.value })}
              placeholder="Enter sequence description"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              onFocus={(e) => e.target.select()}
            />
          </div>
        </div>


      </div>

      {/* Steps */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h4 className="text-md font-medium text-gray-900">Integration Steps</h4>
          <button
            onClick={addStep}
            className="flex items-center space-x-1 px-3 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700"
          >
            <PlusIcon className="w-4 h-4" />
            <span>Add Step</span>
          </button>
        </div>

        {sequence.steps.map((step, index) => (
          <div key={index} className="bg-white border border-gray-200 rounded-lg">
            {/* Step Header */}
            <div className="flex items-center justify-between p-4 border-b border-gray-200">
              <div className="flex items-center space-x-3">
                <button
                  onClick={() => toggleStepExpanded(index)}
                  className="p-1 text-gray-400 hover:text-gray-600"
                >
                  {expandedSteps.has(index) ? (
                    <ChevronDownIcon className="w-4 h-4" />
                  ) : (
                    <ChevronRightIcon className="w-4 h-4" />
                  )}
                </button>
                <div className="flex items-center space-x-2">
                  <span className="text-sm font-medium text-gray-900">Step {step.sequence_order}</span>
                  <input
                    type="text"
                    value={step.name}
                    onChange={(e) => updateStep(index, 'name', e.target.value)}
                    className="text-sm font-medium text-gray-900 bg-transparent border-none focus:outline-none focus:ring-0 min-w-0 flex-1"
                    placeholder="Name (optional)"
                    onFocus={(e) => e.target.select()}
                  />
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => updateStep(index, 'is_active', !step.is_active)}
                    title={step.is_active ? 'Disable step' : 'Enable step'}
                    className={`p-1 rounded ${
                      step.is_active ? 'text-green-600' : 'text-gray-400'
                    }`}
                  >
                    {step.is_active ? (
                      <PlayIcon className="w-4 h-4" />
                    ) : (
                      <PauseIcon className="w-4 h-4" />
                    )}
                  </button>
                  <button
                    onClick={() => duplicateStep(index)}
                    title="Duplicate step"
                    className="p-1 text-gray-500 hover:text-gray-700"
                  >
                    <ArrowPathIcon className="w-4 h-4" />
                  </button>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => removeStep(index)}
                  className="p-1 text-red-600 hover:text-red-800"
                  title="Remove Step"
                >
                  <TrashIcon className="w-4 h-4" />
                </button>
                <button
                  onClick={() => { setCurlTargetIndex(index); setShowCurlModal(true); }}
                  className="px-2 py-1 text-xs text-white bg-indigo-600 rounded hover:bg-indigo-700"
                  title="Paste cURL to prefill"
                >
                  Paste cURL
                </button>
              </div>
            </div>

            {/* Step Configuration */}
            {expandedSteps.has(index) && (
              <div className="p-4 space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Integration Type</label>
                    <select
                      value={step.integration_type}
                      onChange={(e) => updateStep(index, 'integration_type', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      {getIntegrationTypeOptions().map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">HTTP Method</label>
                    <select
                      value={step.http_method}
                      onChange={(e) => updateStep(index, 'http_method', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      {getHttpMethodOptions().map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Auth Type</label>
                    <select
                      value={step.auth_type}
                      onChange={(e) => updateStep(index, 'auth_type', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      {getAuthTypeOptions().map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">API Endpoint</label>
                  <div className="flex space-x-2">
                    <div className="flex-1 relative">
                      <input
                        type="text"
                        value={step.api_endpoint}
                        onChange={(e) => updateStep(index, 'api_endpoint', e.target.value)}
                        placeholder="/leads or https://api.lender.com/leads"
                        className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 ${isValidEndpoint(step.api_endpoint) ? 'border-gray-300 focus:ring-blue-500' : 'border-red-400 focus:ring-red-500'}`}
                        onFocus={(e) => e.target.select()}
                      />
                      {step.api_endpoint && step.api_endpoint.startsWith('http') && (
                        <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
                          <GlobeAltIcon className="h-4 w-4 text-gray-400" />
                        </div>
                      )}
                    </div>
                    {step.api_endpoint && step.api_endpoint.startsWith('http') && (
                      <button
                        onClick={() => validateDns(step.api_endpoint, index)}
                        disabled={dnsValidationStatus[index]?.loading}
                        className="px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        title="Validate DNS resolution - Check if the hostname can be resolved and reached"
                      >
                        {dnsValidationStatus[index]?.loading ? (
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                        ) : (
                          <GlobeAltIcon className="w-4 h-4" />
                        )}
                      </button>
                    )}
                  </div>
                  {!isValidEndpoint(step.api_endpoint) && (
                    <p className="mt-1 text-xs text-red-600">Enter a valid absolute URL or a path starting with /</p>
                  )}
                  {dnsValidationStatus[index] && (
                    <div className={`mt-1 text-xs ${dnsValidationStatus[index].valid ? 'text-green-600' : 'text-red-600'}`}>
                      {dnsValidationStatus[index].message}
                    </div>
                  )}
                </div>

                {/* Auth Configuration */}
                {step.auth_type === 'API_KEY' && (
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">API Key Name</label>
                      <input
                        type="text"
                        value={(step.auth_config && step.auth_config.key_name) || 'X-API-Key'}
                        onChange={(e) => updateAuthConfig(index, { key_name: e.target.value })}
                        placeholder="X-API-Key"
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">API Key Value</label>
                      <input
                        type="text"
                        value={(step.auth_config && (step.auth_config.key_value || step.auth_config.api_key)) || ''}
                        onChange={(e) => updateAuthConfig(index, { key_value: e.target.value })}
                        placeholder="paste your API key"
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Key Location</label>
                      <select
                        value={(step.auth_config && step.auth_config.key_location) || 'header'}
                        onChange={(e) => updateAuthConfig(index, { key_location: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="header">Header</option>
                        <option value="query">Query</option>
                        <option value="body">Body</option>
                      </select>
                    </div>
                  </div>
                )}
                {step.auth_type === 'NONE' && (
                  <div className="p-3 rounded border border-dashed border-gray-300 bg-gray-50 text-sm text-gray-600">
                    This step does not require authentication.
                  </div>
                )}

                {/* Dependencies */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="block text-sm font-medium text-gray-700">Dependencies (from previous steps)</label>
                    <button
                      onClick={() => addDependency(index)}
                      className="flex items-center space-x-1 text-blue-600 hover:text-blue-800"
                    >
                      <PlusIcon className="w-4 h-4" />
                      <span>Add</span>
                    </button>
                  </div>
                  <div className="space-y-2">
                    {Object.entries(step.depends_on_fields).map(([key, value], depIndex) => (
                      <div key={depIndex} className="flex space-x-2">
                        <input
                          type="text"
                          value={key}
                          onChange={(e) => updateDependency(index, key, e.target.value, value)}
                          placeholder="Field name"
                          className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                        <span className="flex items-center text-gray-500">←</span>
                        <input
                          type="text"
                          value={value}
                          onChange={(e) => updateDependency(index, key, key, e.target.value)}
                          placeholder="Source field"
                          className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                        <button
                          onClick={() => removeDependency(index, key)}
                          className="p-2 text-red-600 hover:text-red-800"
                        >
                          <TrashIcon className="w-4 h-4" />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Output Fields */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="block text-sm font-medium text-gray-700">Output Fields (to extract from response)</label>
                    <button
                      onClick={() => addOutputField(index)}
                      className="flex items-center space-x-1 text-blue-600 hover:text-blue-800"
                    >
                      <PlusIcon className="w-4 h-4" />
                      <span>Add</span>
                    </button>
                  </div>
                  <div className="mb-2">
                    <button onClick={() => suggestOutputsFromLastRun(index)} className="text-xs text-indigo-600 hover:text-indigo-800">Suggest from latest run</button>
                  </div>
                  <div className="space-y-2">
                    {step.output_fields.map((field, fieldIndex) => (
                      <div key={fieldIndex} className="flex space-x-2">
                        <input
                          type="text"
                          value={field}
                          onChange={(e) => updateOutputField(index, fieldIndex, e.target.value)}
                          placeholder="$.data.id"
                          className={`flex-1 px-3 py-2 border rounded-md focus:outline-none focus:ring-2 ${isValidJsonPath(field) ? 'border-gray-300 focus:ring-blue-500' : 'border-red-400 focus:ring-red-500'}`}
                        />
                        <button
                          onClick={() => removeOutputField(index, fieldIndex)}
                          className="p-2 text-red-600 hover:text-red-800"
                        >
                          <TrashIcon className="w-4 h-4" />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Request Query Params */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="block text-sm font-medium text-gray-700">Request Query Params</label>
                    <button
                      onClick={() => {
                        const step = sequence.steps[index];
                        const schema = { ...(step.request_schema || {}) } as any;
                        const qp = { ...(schema.query_params || {}) } as Record<string, string>;
                        let newKey = 'param';
                        let suffix = 1;
                        while (qp[newKey]) { newKey = `param_${suffix++}`; }
                        qp[newKey] = '';
                        schema.query_params = qp;
                        updateStep(index, 'request_schema', schema);
                      }}
                      className="flex items-center space-x-1 text-blue-600 hover:text-blue-800"
                    >
                      <PlusIcon className="w-4 h-4" />
                      <span>Add</span>
                    </button>
                  </div>
                  <div className="space-y-2">
                    {Object.entries(((sequence.steps[index].request_schema || {}) as any).query_params || {}).map(([pKey, pVal]: [string, any], pIndex: number) => (
                      <div key={`${pKey}-${pIndex}`} className="flex space-x-2">
                        <input
                          type="text"
                          value={pKey}
                          onChange={(e) => {
                            const step = sequence.steps[index];
                            const schema = { ...(step.request_schema || {}) } as any;
                            const qp = { ...(schema.query_params || {}) } as Record<string, string>;
                            const oldVal = qp[pKey];
                            delete qp[pKey];
                            qp[e.target.value] = String(oldVal ?? '');
                            schema.query_params = qp;
                            updateStep(index, 'request_schema', schema);
                          }}
                          placeholder="Param name"
                          className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                        <input
                          type="text"
                          value={String(pVal ?? '')}
                          onChange={(e) => {
                            const step = sequence.steps[index];
                            const schema = { ...(step.request_schema || {}) } as any;
                            const qp = { ...(schema.query_params || {}) } as Record<string, string>;
                            qp[pKey] = e.target.value;
                            schema.query_params = qp;
                            updateStep(index, 'request_schema', schema);
                          }}
                          placeholder="Param value"
                          className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                        <button
                          onClick={() => {
                            const step = sequence.steps[index];
                            const schema = { ...(step.request_schema || {}) } as any;
                            const qp = { ...(schema.query_params || {}) } as Record<string, string>;
                            delete qp[pKey];
                            schema.query_params = qp;
                            updateStep(index, 'request_schema', schema);
                          }}
                          className="p-2 text-red-600 hover:text-red-800"
                        >
                          <TrashIcon className="w-4 h-4" />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Request Headers */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="block text-sm font-medium text-gray-700">Request Headers</label>
                    <button onClick={() => addHeader(index)} className="flex items-center space-x-1 text-blue-600 hover:text-blue-800">
                      <PlusIcon className="w-4 h-4" />
                      <span>Add</span>
                    </button>
                  </div>
                  <div className="space-y-2">
                    {Object.entries(sequence.steps[index].request_headers || {}).map(([hKey, hVal], hIndex) => (
                      <div key={hIndex} className="flex space-x-2">
                        <input
                          type="text"
                          value={hKey}
                          onChange={(e) => updateHeader(index, hKey, e.target.value, String(hVal))}
                          placeholder="Header name"
                          className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                        <input
                          type="text"
                          value={String(hVal)}
                          onChange={(e) => updateHeader(index, hKey, hKey, e.target.value)}
                          placeholder="Header value"
                          className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                        <button
                          onClick={() => removeHeader(index, hKey)}
                          className="p-2 text-red-600 hover:text-red-800"
                        >
                          <TrashIcon className="w-4 h-4" />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Body Template (JSON) */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Body Template (JSON)</label>
                  <textarea
                    value={templateText[index] !== undefined ? templateText[index] : JSON.stringify((sequence.steps[index].request_schema && sequence.steps[index].request_schema.template) || {}, null, 2)}
                    onChange={(e) => handleTemplateChange(index, e.target.value)}
                    rows={6}
                    className={`w-full font-mono text-sm px-3 py-2 border rounded-md focus:outline-none focus:ring-2 ${templateError[index] ? 'border-red-400 focus:ring-red-500' : 'border-gray-300 focus:ring-blue-500'}`}
                  />
                  {templateError[index] && (
                    <p className="mt-1 text-xs text-red-600">{templateError[index]}</p>
                  )}
                </div>

                {/* Step Advanced Settings */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Timeout (s)</label>
                    <input
                      type="number"
                      min={1}
                      value={step.timeout_seconds ?? 30}
                      onChange={(e) => updateStep(index, 'timeout_seconds', Number(e.target.value))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Retries</label>
                    <input
                      type="number"
                      min={0}
                      value={step.retry_count ?? 3}
                      onChange={(e) => updateStep(index, 'retry_count', Number(e.target.value))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Retry Delay (s)</label>
                    <input
                      type="number"
                      min={0}
                      value={step.retry_delay_seconds ?? 5}
                      onChange={(e) => updateStep(index, 'retry_delay_seconds', Number(e.target.value))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Rate Limit (/min)</label>
                    <input
                      type="number"
                      min={0}
                      value={step.rate_limit_per_minute ?? 0}
                      onChange={(e) => updateStep(index, 'rate_limit_per_minute', Number(e.target.value))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>
              </div>
            )}
          </div>
        ))}

        {/* Empty State */}
        {sequence.steps.length === 0 && (
          <div className="text-center py-8 bg-white border border-gray-200 rounded-lg">
            <ArrowPathIcon className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No integration steps</h3>
            <p className="mt-1 text-sm text-gray-500">
              Get started by adding your first integration step.
            </p>
            <div className="mt-6">
              <button
                onClick={addStep}
                className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
              >
                <PlusIcon className="w-4 h-4 mr-2" />
                Add Step
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Paste cURL Modal */}
      {showCurlModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-30">
          <div className="bg-white rounded-lg shadow p-4 w-full max-w-2xl">
            <h4 className="text-md font-medium text-gray-900 mb-2">Paste cURL</h4>
            <textarea value={curlText} onChange={(e) => setCurlText(e.target.value)} rows={8} className="w-full font-mono text-sm px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="curl 'https://api.example.com/endpoint' -X POST -H 'Content-Type: application/json' --data-raw '{...}'" />
            <div className="mt-3 flex justify-end space-x-2">
              <button onClick={() => setShowCurlModal(false)} className="px-3 py-1 text-sm text-gray-700">Cancel</button>
              <button onClick={() => applyCurlToStep(curlTargetIndex ?? Math.max(0, (sequence.steps.length - 1)))} className="px-3 py-1 text-sm text-white bg-indigo-600 rounded">Apply</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SequenceBuilder;
